# whatsapp/webhook.py

import re
import requests
from whatsapp.templates import (
    manager_trip_planned_message,
    driver_trip_assigned_message,
    customer_load_request_message,
    enroute_load_offer_message
)
from agent.agent_loop import plan_trip_with_truck, accept_trip, start_trip
from database.models import db

def geocode_city(city_name):
    """
    Geocode city name to coordinates using GraphHopper Geocoding API
    Falls back to Nominatim if GraphHopper fails
    """
    # Try GraphHopper first
    try:
        url = "https://graphhopper.com/api/1/geocode"
        params = {
            "q": city_name + ", India",
            "limit": 1,
            "locale": "en"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("hits") and len(data["hits"]) > 0:
            hit = data["hits"][0]
            point = hit["point"]
            lat, lon = point["lat"], point["lng"]
            print(f"✓ GraphHopper found {city_name}: ({lat}, {lon})")
            return (lat, lon)
    except Exception as e:
        print(f"GraphHopper geocoding failed for {city_name}: {e}")
    
    # Fallback to Nominatim
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": city_name + ", India",
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "AI-Logistics-Agent/2.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f"✓ Nominatim found {city_name}: ({lat}, {lon})")
            return (lat, lon)
    except Exception as e:
        print(f"Nominatim geocoding failed for {city_name}: {e}")
    
    return None

def detect_user_role(phone_number):
    """Detect user role from phone number"""
    # In production, this would query the database
    # For now, using simple logic:
    # Manager: +919999999999
    # Drivers: Check if they have assigned trucks
    # Others: Customer
    
    if phone_number == "+919999999999":
        return "manager"
    
    # Check if user is a driver
    trucks = db.get_all_trucks()
    for truck in trucks:
        if truck.get('driver_phone') == phone_number:
            return "driver"
    
    return "customer"

def handle_message(message: str, phone_number: str = "+919999999999"):
    """Handle incoming WhatsApp messages based on user role"""
    message = message.strip()
    role = detect_user_role(phone_number)
    
    # ========== MANAGER COMMANDS ==========
    if role == "manager":
        # START TRIP FROM X TO Y
        match = re.search(
            r"start\s+trip\s+from\s+(.+?)\s+to\s+(.+)",
            message,
            re.IGNORECASE
        )
        
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            
            # Plan trip with truck selection
            trip, error = plan_trip_with_truck(origin, destination)
            
            if error:
                return f"❌ {error}"
            
            # Return manager view
            return manager_trip_planned_message(trip)
    
    # ========== DRIVER COMMANDS ==========
    elif role == "driver":
        msg_lower = message.lower()
        
        # Get driver's active trip
        active_trips = db.get_active_trips()
        driver_trip = None
        for trip in active_trips:
            if trip.get('driver_phone') == phone_number:
                driver_trip = trip
                break
        
        # START - Accept and start trip
        if msg_lower in ["1", "start", "1️⃣ start"]:
            if not driver_trip:
                return "❌ No trip assigned to you"
            
            success, msg = accept_trip(driver_trip['id'], phone_number)
            if not success:
                return f"❌ {msg}"
            
            start_trip(driver_trip['id'], driver_trip['origin'])
            return "✅ Trip started! Safe journey! 🚚\n\nReply ARRIVED when you reach destination."
        
        # SHARE LOCATION
        elif msg_lower in ["2", "share location", "2️⃣ share location", "location"]:
            if not driver_trip:
                return "❌ No active trip"
            
            # Generate location sharing link
            location_link = f"https://maps.google.com/?q={driver_trip['origin']}"
            return (
                f"📍 Location Sharing Active\n\n"
                f"Share this link with customers:\n"
                f"{location_link}\n\n"
                f"Current: {driver_trip.get('current_location', driver_trip['origin'])}\n"
                f"Destination: {driver_trip['destination']}"
            )
        
        # DELAY
        elif msg_lower in ["3", "delay", "3️⃣ delay"]:
            if not driver_trip:
                return "❌ No active trip"
            
            return (
                "⏰ Delay Notification\n\n"
                "How long is the delay?\n"
                "Reply: DELAY <hours> <reason>\n\n"
                "Example: DELAY 2 Traffic jam"
            )
        
        # ARRIVED
        elif msg_lower in ["arrived", "reached", "done"]:
            if not driver_trip:
                return "❌ No active trip"
            
            db.update_trip_status(driver_trip['id'], 'completed', driver_trip['destination'])
            db.update_truck_status(driver_trip['truck_id'], 'available', driver_trip['destination'])
            
            return (
                "✅ Trip Completed!\n\n"
                f"From: {driver_trip['origin']}\n"
                f"To: {driver_trip['destination']}\n"
                f"Distance: {driver_trip['distance_km']} km\n\n"
                "Well done! 🎉"
            )
        
        # Default: Show driver their current trip
        else:
            if driver_trip:
                return driver_trip_assigned_message(driver_trip)
            else:
                return (
                    "👋 Hi Driver!\n\n"
                    "No active trips assigned.\n"
                    "You'll receive a notification when a trip is assigned."
                )
    
    # ========== CUSTOMER COMMANDS ==========
    elif role == "customer":
        # LOAD command
        match = re.search(
            r"load\s+(\d+)\s*kg\s+(.+?)\s+to\s+(.+)",
            message,
            re.IGNORECASE
        )
        
        if match:
            weight = int(match.group(1))
            pickup = match.group(2).strip()
            dropoff = match.group(3).strip()
            
            # Create load request
            load_data = {
                'weight_kg': weight,
                'pickup': pickup,
                'dropoff': dropoff,
                'customer_phone': phone_number
            }
            
            load = db.create_load_request(load_data)
            
            # Check for en-route trucks
            active_trips = db.get_active_trips()
            matching_trips = []
            
            for trip in active_trips:
                # Simple matching: check if pickup/dropoff are on route
                if pickup.lower() in trip['origin'].lower() or pickup.lower() in trip['destination'].lower():
                    capacity_left = 100 - trip['load_percent']
                    if capacity_left >= 20:  # At least 20% capacity
                        matching_trips.append(trip)
            
            if matching_trips:
                # Offer to nearest truck
                trip = matching_trips[0]
                return enroute_load_offer_message(trip, load)
            else:
                return (
                    f"📦 Load Request Received\n\n"
                    f"Weight: {weight} kg\n"
                    f"Pickup: {pickup}\n"
                    f"Dropoff: {dropoff}\n\n"
                    f"Load ID: {load['id']}\n\n"
                    "🔍 Searching for available trucks...\n"
                    "You'll be notified when a truck is assigned."
                )
        
        # Help for customers
        else:
            return customer_load_request_message()
    
    # ========== HELP / DEFAULT ==========
    if message.lower() in ["hi", "hello", "start", "help", "menu"]:
        if role == "manager":
            return (
                "👋 *Hi Manager!*\n\n"
                "📋 *Available Commands:*\n\n"
                "1. Plan a trip:\n"
                "   `START TRIP FROM Mumbai TO Delhi`\n\n"
                "2. Check fleet status:\n"
                "   `FLEET STATUS`\n\n"
                "3. View active trips:\n"
                "   `ACTIVE TRIPS`\n\n"
                "Try: `START TRIP FROM Pune TO Nagpur`"
            )
        elif role == "driver":
            return (
                "👋 *Hi Driver!*\n\n"
                "📋 *Available Commands:*\n\n"
                "When trip assigned:\n"
                "1️⃣ START - Accept & start trip\n"
                "2️⃣ SHARE LOCATION - Share live location\n"
                "3️⃣ DELAY - Report delay\n\n"
                "ARRIVED - Mark trip complete"
            )
        else:
            return customer_load_request_message()
    
    # Unknown command
    return (
        "🤖 *I didn't understand that command.*\n\n"
        "Type `HELP` for available commands."
    )

def test_webhook():
    """Test the webhook with sample messages"""
    print("\n" + "="*50)
    print("TESTING MANAGER")
    print("="*50)
    print(handle_message("START TRIP FROM Mumbai TO Delhi", "+919999999999"))
    
    print("\n" + "="*50)
    print("TESTING DRIVER")
    print("="*50)
    print(handle_message("1", "+919876543210"))
    
    print("\n" + "="*50)
    print("TESTING CUSTOMER")
    print("="*50)
    print(handle_message("LOAD 500kg Mumbai to Pune", "+918888888888"))

if __name__ == "__main__":
    test_webhook()
