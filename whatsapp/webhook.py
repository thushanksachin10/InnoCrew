# whatsapp/webhook.py

import re
import requests
from whatsapp.templates import (
    manager_trip_planned_message,
    driver_trip_assigned_message,
    customer_load_request_message,
    enroute_load_offer_message
)
from database.models import db
from logging_config import get_logger

logger = get_logger(__name__)

def handle_message(message: str, phone_number: str = "+919999999999"):
    """Handle incoming WhatsApp messages based on user role"""
    logger.info(f"Processing message from {phone_number}: '{message}'")
    
    message = message.strip()
    role = detect_user_role(phone_number)
    logger.debug(f"Detected user role: {role}")

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

def plan_trip_with_truck(origin, destination, waypoints=None):
    """Plan a complete trip with truck selection"""
    from agent.agent_loop import plan_trip_with_truck as plan_actual
    return plan_actual(origin, destination, waypoints)

def accept_trip(trip_id, driver_phone):
    """Driver accepts the trip"""
    from agent.agent_loop import accept_trip as accept_actual
    return accept_actual(trip_id, driver_phone)

def start_trip(trip_id, location):
    """Driver starts the trip"""
    from agent.agent_loop import start_trip as start_actual
    return start_actual(trip_id, location)

def complete_trip(trip_id, location):
    """Driver completes the trip"""
    from agent.agent_loop import complete_trip as complete_actual
    return complete_actual(trip_id, location)

def update_trip_location(trip_id, location):
    """Update trip's current location"""
    from agent.agent_loop import update_trip_location as update_actual
    return update_actual(trip_id, location)

def find_enroute_opportunities(truck_id):
    """Find additional load opportunities for a truck already on route"""
    from agent.agent_loop import find_enroute_opportunities as find_actual
    return find_actual(truck_id)

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
        
        # FLEET STATUS command
        elif message.lower() in ["fleet status", "fleet", "trucks"]:
            trucks = db.get_all_trucks()
            
            available = sum(1 for t in trucks if t.get('status') == 'available')
            assigned = sum(1 for t in trucks if t.get('status') == 'assigned')
            in_transit = sum(1 for t in trucks if t.get('status') == 'in_transit')
            
            response = (
                f"🚛 *Fleet Status*\n\n"
                f"Total Trucks: {len(trucks)}\n"
                f"✅ Available: {available}\n"
                f"📋 Assigned: {assigned}\n"
                f"🚚 In Transit: {in_transit}\n\n"
            )
            
            # Show individual truck status
            for truck in trucks[:5]:  # Show first 5 trucks
                status_emoji = "✅" if truck.get('status') == 'available' else "🚚" if truck.get('status') == 'in_transit' else "📋"
                response += f"{status_emoji} {truck.get('number')} - {truck.get('location')} ({truck.get('status')})\n"
            
            if len(trucks) > 5:
                response += f"\n... and {len(trucks) - 5} more trucks"
            
            return response
        
        # ACTIVE TRIPS command
        elif message.lower() in ["active trips", "trips", "all trips"]:
            active_trips = db.get_active_trips()
            
            if not active_trips:
                return "📭 *No Active Trips*\n\nNo trips are currently active. Create a new trip with `START TRIP FROM ...`"
            
            response = f"📍 *Active Trips ({len(active_trips)})*\n\n"
            
            for trip in active_trips:
                status_emoji = "📋" if trip.get('status') == 'pending' else "🚚" if trip.get('status') == 'in_progress' else "✅"
                response += (
                    f"{status_emoji} *{trip.get('origin')} → {trip.get('destination')}*\n"
                    f"   Truck: {trip.get('truck_number')}\n"
                    f"   Driver: {trip.get('driver_name')}\n"
                    f"   Status: {trip.get('status')}\n"
                    f"   Progress: {trip.get('progress_percent', 0)}%\n\n"
                )
            
            return response
    
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
        if msg_lower in ["1", "start", "1️⃣ start", "accept"]:
            if not driver_trip:
                return "❌ No trip assigned to you"
            
            success, msg = accept_trip(driver_trip['id'], phone_number)
            if not success:
                return f"❌ {msg}"
            
            # Start the trip
            start_trip(driver_trip['id'], driver_trip['origin'])
            return "✅ Trip started! Safe journey! 🚚\n\n*Commands:*\n📍 LOCATION - Update location\n📊 STATUS - Check trip status\n✅ ARRIVED - Mark as completed"
        
        # SHARE LOCATION / UPDATE LOCATION
        elif msg_lower in ["2", "share location", "2️⃣ share location", "location", "update location"]:
            if not driver_trip:
                return "❌ No active trip"
            
            # Check if location is provided
            location_match = re.search(r"location\s+(.+)", message, re.IGNORECASE)
            if location_match:
                location = location_match.group(1).strip()
                success, msg = update_trip_location(driver_trip['id'], location)
                if success:
                    return f"📍 Location updated to: {location}\n\nProgress: {msg.split('(')[-1].split(')')[0]}"
                else:
                    return f"❌ {msg}"
            
            # Generate location sharing link
            current_location = driver_trip.get('current_location', driver_trip['origin'])
            location_link = f"https://maps.google.com/?q={current_location}"
            return (
                f"📍 *Current Location*\n\n"
                f"Share this link:\n{location_link}\n\n"
                f"*Current:* {current_location}\n"
                f"*Destination:* {driver_trip['destination']}\n"
                f"*Progress:* {driver_trip.get('progress_percent', 0)}%\n\n"
                f"To update location, send:\n`LOCATION <city name>`\n\n"
                f"Example: `LOCATION Vadodara`"
            )
        
        # DELAY
        elif msg_lower in ["3", "delay", "3️⃣ delay"]:
            if not driver_trip:
                return "❌ No active trip"
            
            # Check if delay details are provided
            delay_match = re.search(r"delay\s+(\d+)\s*(.*)", message, re.IGNORECASE)
            if delay_match:
                hours = delay_match.group(1)
                reason = delay_match.group(2).strip() or "unspecified"
                
                # Update ETA
                new_eta = driver_trip.get('eta_hours', 0) + int(hours)
                
                # In production, update this in database
                return (
                    f"⏰ *Delay Reported*\n\n"
                    f"*Additional Hours:* {hours}\n"
                    f"*Reason:* {reason}\n"
                    f"*New ETA:* {new_eta:.1f} hours\n\n"
                    f"Manager has been notified. Stay safe!"
                )
            
            return (
                "⏰ *Delay Notification*\n\n"
                "How long is the delay?\n"
                "Reply: `DELAY <hours> <reason>`\n\n"
                "*Examples:*\n"
                "• `DELAY 2 Traffic jam`\n"
                "• `DELAY 1 Vehicle breakdown`\n"
                "• `DELAY 3 Heavy rain`"
            )
        
        # ARRIVED
        elif msg_lower in ["arrived", "reached", "done", "complete", "finished"]:
            if not driver_trip:
                return "❌ No active trip"
            
            # Get current location if provided
            location_match = re.search(r"arrived\s+at\s+(.+)", message, re.IGNORECASE)
            location = location_match.group(1).strip() if location_match else driver_trip['destination']
            
            success, msg = complete_trip(driver_trip['id'], location)
            if not success:
                return f"❌ {msg}"
            
            return (
                "✅ *Trip Completed!*\n\n"
                f"*From:* {driver_trip['origin']}\n"
                f"*To:* {location}\n"
                f"*Distance:* {driver_trip['distance_km']} km\n"
                f"*Estimated Profit:* ₹{driver_trip['expected_profit']:,}\n\n"
                "Well done! 🎉\n\n"
                "Check your next assignment soon!"
            )
        
        # STATUS command
        elif msg_lower in ["status", "progress", "check status"]:
            if driver_trip:
                return (
                    f"🚚 *Trip Status*\n\n"
                    f"*Route:* {driver_trip['origin']} → {driver_trip['destination']}\n"
                    f"*Progress:* {driver_trip.get('progress_percent', 0)}%\n"
                    f"*Distance:* {driver_trip['distance_km']} km\n"
                    f"*ETA Remaining:* {driver_trip.get('eta_hours', 0):.1f} hours\n"
                    f"*Current Load:* {driver_trip.get('load_percent', 0)}%\n"
                    f"*Confidence:* {driver_trip.get('confidence', 0.0)}\n\n"
                    f"*Next Fuel Stop:* {driver_trip.get('fuel_stops', [{}])[0].get('city', 'None planned')}\n\n"
                    f"*Truck:* {driver_trip.get('truck_number')}\n"
                    f"*Condition:* {driver_trip.get('condition')}\n"
                    f"*Mileage:* {driver_trip.get('mileage')} km/l"
                )
            else:
                return (
                    "👋 *Hi Driver!*\n\n"
                    "No active trips assigned.\n"
                    "You'll receive a notification when a trip is assigned.\n\n"
                    "*Your Truck:*\n"
                )
        
        # Default: Show driver their current trip
        else:
            if driver_trip:
                return driver_trip_assigned_message(driver_trip)
            else:
                # Get driver's truck info
                trucks = db.get_all_trucks()
                driver_truck = None
                for truck in trucks:
                    if truck.get('driver_phone') == phone_number:
                        driver_truck = truck
                        break
                
                if driver_truck:
                    return (
                        f"👋 *Hi {driver_truck.get('driver_name', 'Driver')}!*\n\n"
                        f"*Your Truck:* {driver_truck.get('number')}\n"
                        f"*Status:* {driver_truck.get('status', 'available')}\n"
                        f"*Location:* {driver_truck.get('location', 'Unknown')}\n"
                        f"*Fuel:* {driver_truck.get('fuel_percent', 0)}%\n\n"
                        "No active trips assigned.\n"
                        "You'll receive a notification when a trip is assigned."
                    )
                else:
                    return (
                        "👋 *Hi Driver!*\n\n"
                        "No truck assigned to you.\n"
                        "Please contact your manager."
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
                'customer_phone': phone_number,
                'status': 'pending',
                'rate_per_kg': 12  # Default rate ₹12/kg
            }
            
            load = db.create_load_request(load_data)
            
            # Check for en-route trucks
            active_trips = db.get_active_trips()
            matching_trips = []
            
            for trip in active_trips:
                # Simple matching: check if pickup/dropoff are on route
                pickup_lower = pickup.lower()
                if (pickup_lower in trip['origin'].lower() or 
                    pickup_lower in trip['destination'].lower() or
                    any(pickup_lower in wp.lower() for wp in trip.get('waypoints', []))):
                    
                    capacity_left = 100 - trip.get('load_percent', 0)
                    available_capacity = trip.get('available_capacity_kg', 0)
                    
                    if capacity_left >= 20 and available_capacity >= weight:
                        matching_trips.append(trip)
            
            if matching_trips:
                # Offer to nearest truck
                trip = matching_trips[0]
                return enroute_load_offer_message(trip, load)
            else:
                # Calculate estimated cost
                estimated_distance = 500  # Simplified
                estimated_cost = weight * 12  # ₹12 per kg
                
                return (
                    f"📦 *Load Request Received*\n\n"
                    f"*Weight:* {weight} kg\n"
                    f"*Pickup:* {pickup}\n"
                    f"*Dropoff:* {dropoff}\n"
                    f"*Estimated Cost:* ₹{estimated_cost:,}\n\n"
                    f"*Load ID:* {load.get('id', 'N/A')}\n\n"
                    "🔍 *Searching for available trucks...*\n"
                    "You'll be notified when a truck is assigned.\n\n"
                    "To check status, reply:\n`STATUS {load_id}`"
                )
        
        # CHECK STATUS command
        elif "status" in msg_lower:
            # Try to extract load ID
            match = re.search(r"status\s+(\w+)", msg_lower)
            if match:
                load_id = match.group(1).upper()
                loads = db._load_json(db.loads_file)
                for load in loads:
                    if load.get('id') == load_id:
                        return (
                            f"📦 *Load Status*\n\n"
                            f"*ID:* {load_id}\n"
                            f"*Weight:* {load.get('weight_kg')} kg\n"
                            f"*Route:* {load.get('pickup')} → {load.get('dropoff')}\n"
                            f"*Status:* {load.get('status', 'pending')}\n"
                            f"*Created:* {load.get('created_at', 'Unknown')}\n\n"
                            f"{'🚚 Truck assigned: ' + load.get('truck_id', 'N/A') if load.get('status') == 'assigned' else '⏳ Waiting for truck assignment'}"
                        )
            
            return (
                "📋 *Check Load Status*\n\n"
                "To check your load status, reply:\n"
                "`STATUS <load_id>`\n\n"
                "Example: `STATUS LOAD001`\n\n"
                "Don't know your Load ID?\n"
                "Contact support or create a new load request."
            )
        
        # Help for customers
        else:
            return customer_load_request_message()
    
    # ========== HELP / DEFAULT ==========
    if message.lower() in ["hi", "hello", "start", "help", "menu", "commands"]:
        if role == "manager":
            return (
                "👋 *Hi Manager!*\n\n"
                "📋 *Available Commands:*\n\n"
                "1. Plan a trip:\n"
                "   `START TRIP FROM Mumbai TO Delhi`\n\n"
                "2. Check fleet status:\n"
                "   `FLEET STATUS` or `FLEET`\n\n"
                "3. View active trips:\n"
                "   `ACTIVE TRIPS` or `TRIPS`\n\n"
                "4. Get help:\n"
                "   `HELP` or `COMMANDS`\n\n"
                "*Try:* `START TRIP FROM Pune TO Nagpur`"
            )
        elif role == "driver":
            return (
                "👋 *Hi Driver!*\n\n"
                "📋 *Available Commands:*\n\n"
                "When trip assigned:\n"
                "• `START` or `1` - Accept & start trip\n"
                "• `LOCATION <city>` - Update location\n"
                "• `DELAY <hours> <reason>` - Report delay\n"
                "• `STATUS` - Check trip progress\n"
                "• `ARRIVED` - Mark trip complete\n\n"
                "General:\n"
                "• `HELP` - Show this message"
            )
        else:
            return customer_load_request_message()
    
    # Unknown command
    return (
        "🤖 *I didn't understand that command.*\n\n"
        "Type `HELP` for available commands.\n\n"
        "*Quick Examples:*\n"
        "• `START TRIP FROM Mumbai TO Delhi` (Manager)\n"
        "• `LOAD 500kg Pune TO Mumbai` (Customer)\n"
        "• `STATUS` (Driver)"
    )

def test_webhook():
    """Test the webhook with sample messages"""
    print("\n" + "="*50)
    print("TESTING MANAGER")
    print("="*50)
    print(handle_message("START TRIP FROM Mumbai TO Delhi", "+919999999999"))
    print("\n" + "-"*30)
    print(handle_message("FLEET STATUS", "+919999999999"))
    print("\n" + "-"*30)
    print(handle_message("ACTIVE TRIPS", "+919999999999"))
    
    print("\n" + "="*50)
    print("TESTING DRIVER")
    print("="*50)
    print(handle_message("1", "+919876543210"))
    print("\n" + "-"*30)
    print(handle_message("STATUS", "+919876543210"))
    print("\n" + "-"*30)
    print(handle_message("LOCATION Vadodara", "+919876543210"))
    
    print("\n" + "="*50)
    print("TESTING CUSTOMER")
    print("="*50)
    print(handle_message("LOAD 500kg Mumbai to Pune", "+918888888888"))
    print("\n" + "-"*30)
    print(handle_message("HELP", "+918888888888"))

if __name__ == "__main__":
    test_webhook()