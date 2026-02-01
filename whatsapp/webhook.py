# whatsapp/webhook.py

import re
import requests
from whatsapp.templates import (
    manager_trip_planned_message,
    driver_trip_assigned_message,
    customer_load_request_message,
    enroute_load_offer_message,
    business_opportunity_message,
    load_rate_quote_message
)
from whatsapp.business_notifications import (
    send_business_notifications,
    handle_business_response,
    handle_manager_load_approval
)
from database.models import db
from logging_config import get_logger

logger = get_logger(__name__)

def geocode_city(city_name):
    """
    Geocode city name to coordinates using GraphHopper Geocoding API
    Falls back to Nominatim if GraphHopper fails
    """
    logger.info(f"Geocoding city: {city_name}")
    
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
            logger.info(f"✓ GraphHopper found {city_name}: ({lat}, {lon})")
            return (lat, lon)
    except Exception as e:
        logger.warning(f"GraphHopper geocoding failed for {city_name}: {e}")
    
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
            logger.info(f"✓ Nominatim found {city_name}: ({lat}, ({lon})")
            return (lat, lon)
    except Exception as e:
        logger.warning(f"Nominatim geocoding failed for {city_name}: {e}")
    
    logger.error(f"❌ Could not geocode city: {city_name}")
    return None

def plan_trip_with_truck(origin, destination, waypoints=None):
    """Plan a complete trip with truck selection"""
    from agent.agent_loop import plan_trip_with_truck as plan_actual
    logger.info(f"Planning trip: {origin} → {destination}")
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
    logger.debug(f"Detecting role for phone: {phone_number}")
    
    # First check users.json database
    users = db._load_json(db.users_file)
    
    for user in users:
        if user.get('phone') == phone_number:
            role = user.get('role', 'customer')
            logger.debug(f"Found in users.json: {role}")
            return role
    
    # Fallback: Check if user is a driver from trucks
    trucks = db.get_all_trucks()
    for truck in trucks:
        if truck.get('driver_phone') == phone_number:
            logger.debug(f"Found as driver in trucks")
            return "driver"
    
    # Default to regular customer
    logger.debug(f"Defaulting to customer role")
    return "customer"

def extract_trip_details(message):
    """Extract origin and destination from various trip command formats"""
    patterns = [
        r"start\s+trip\s+from\s+(.+?)\s+to\s+(.+)",
        r"START\s+TRIP\s+FROM\s+(.+?)\s+TO\s+(.+)",
        r"start\s+trip\s+(.+?)\s+to\s+(.+)",
        r"plan\s+trip\s+(.+?)\s+to\s+(.+)",
        r"trip\s+(.+?)\s+to\s+(.+)",
        r"create\s+trip\s+(.+?)\s+to\s+(.+)",
        r"from\s+(.+?)\s+to\s+(.+)",
        r"(.+?)\s+to\s+(.+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            
            # Clean up the text
            origin = clean_city_name(origin)
            destination = clean_city_name(destination)
            
            # Skip if it looks like other commands
            if any(word in origin.lower() for word in ["help", "fleet", "status", "active", "trips"]):
                continue
            
            return origin, destination
    
    return None

def clean_city_name(city):
    """Clean city names from command keywords"""
    city = city.replace('from ', '').replace('FROM ', '')
    city = city.replace('trip ', '').replace('TRIP ', '')
    city = city.replace('start ', '').replace('START ', '')
    city = city.replace('plan ', '').replace('PLAN ', '')
    city = city.replace('create ', '').replace('CREATE ', '')
    return city.strip()

def format_manager_welcome():
    """Format welcome message for manager"""
    return (
        "👋 *Welcome Manager!*\n\n"
        "I'm your AI Logistics Assistant. I can help you:\n\n"
        "🚚 *Plan new trips*\n"
        "📊 *Monitor fleet status*\n"
        "📍 *Track active shipments*\n"
        "🤝 *Manage business opportunities*\n\n"
        "Type `HELP` for available commands.\n\n"
        "*Quick start:* `Mumbai to Delhi`"
    )

def format_manager_help():
    """Format help message with better styling"""
    return (
        "📋 *AI Logistics Agent - Command Guide*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚚 *TRIP PLANNING*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• `START TRIP FROM Mumbai TO Delhi`\n"
        "• `Mumbai to Delhi`\n"
        "• `from Pune to Nagpur`\n"
        "• `trip Chennai to Bangalore`\n\n"
        "📊 *FLEET MANAGEMENT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• `FLEET STATUS` - View all trucks\n"
        "• `FLEET` - Quick fleet overview\n\n"
        "📍 *TRIP MONITORING*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• `ACTIVE TRIPS` - View ongoing shipments\n"
        "• `TRIPS` - All trip information\n\n"
        "🤝 *BUSINESS OPPORTUNITIES*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• `ACCEPT LOAD <ID>` - Accept business load\n"
        "• `REJECT LOAD <ID>` - Reject business load\n"
        "• `BUSINESS LOADS` - View pending loads\n\n"
        "❓ *OTHER COMMANDS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• `HI` - Welcome message\n"
        "• `HELP` - Show this guide\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*You can use ANY Indian city!* 🏙️\n"
        "Delhi • Mumbai • Pune • Bangalore • Chennai\n"
        "Kolkata • Hyderabad • Ahmedabad • Jaipur • Lucknow"
    )

def format_fleet_status():
    """Format fleet status with better styling"""
    trucks = db.get_all_trucks()
    
    available = sum(1 for t in trucks if t.get('status') == 'available')
    assigned = sum(1 for t in trucks if t.get('status') == 'assigned')
    in_transit = sum(1 for t in trucks if t.get('status') == 'in_transit')
    
    response = (
        "🚛 *Fleet Dashboard*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Available:* {available} trucks\n"
        f"📋 *Assigned:* {assigned} trucks\n"
        f"🚚 *In Transit:* {in_transit} trucks\n"
        f"🚛 *Total Fleet:* {len(trucks)} trucks\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    # Show individual trucks (limited to 5 for readability)
    if trucks:
        response += "*Active Trucks:*\n"
        for truck in trucks[:5]:
            status_emoji = "🟢" if truck.get('status') == 'available' else "🟡" if truck.get('status') == 'assigned' else "🔴"
            response += f"{status_emoji} {truck.get('number')} - {truck.get('location')}\n"
        
        if len(trucks) > 5:
            response += f"... and {len(trucks) - 5} more trucks\n"
    
    response += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += "Type `TRIP <city> to <city>` to assign a truck"
    
    return response

def format_active_trips():
    """Format active trips with better styling"""
    active_trips = db.get_active_trips()
    
    if not active_trips:
        return (
            "📍 *Active Trips Dashboard*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📭 *No Active Trips*\n\n"
            "No trucks are currently on route.\n"
            "Plan a new trip with:\n`Mumbai to Delhi`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    
    response = (
        f"📍 *Active Trips ({len(active_trips)})*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for i, trip in enumerate(active_trips, 1):
        status_emoji = "📋" if trip.get('status') == 'pending' else "🚚" if trip.get('status') == 'in_progress' else "✅"
        progress = trip.get('progress_percent', 0)
        progress_bar = get_progress_bar(progress)
        
        response += (
            f"{i}. {status_emoji} *{trip.get('origin')} → {trip.get('destination')}*\n"
            f"   🚛 {trip.get('truck_number')}\n"
            f"   👤 {trip.get('driver_name')}\n"
            f"   📏 {trip.get('distance_km', 0)} km\n"
            f"   {progress_bar} {progress}%\n\n"
        )
    
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    response += "Type `FLEET` to view available trucks"
    
    return response

def format_pending_business_loads():
    """Format pending business loads for manager"""
    try:
        # Get pending business loads
        loads = db.get_pending_business_loads()
        
        if not loads:
            return (
                "📋 *Business Loads Dashboard*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ *No Pending Loads*\n\n"
                "All business loads have been processed.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
        
        response = (
            f"📋 *Business Loads ({len(loads)})*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        for i, load in enumerate(loads, 1):
            response += (
                f"{i}. *Load ID:* {load.get('id', 'N/A')}\n"
                f"   📦 *Weight:* {load.get('weight_kg', 0)} kg\n"
                f"   📍 *Route:* {load.get('pickup', 'N/A')} → {load.get('dropoff', 'N/A')}\n"
                f"   🏢 *Business:* {load.get('business_name', 'N/A')}\n"
                f"   💰 *Rate Quote:* ₹{load.get('rate_per_kg', 0)}/kg\n"
                f"   ⏰ *Created:* {load.get('created_at', 'N/A')}\n\n"
            )
        
        response += (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "*To approve a load:*\n"
            "`ACCEPT LOAD <ID>`\n\n"
            "*To reject a load:*\n"
            "`REJECT LOAD <ID>`\n\n"
            "*Example:* `ACCEPT LOAD BLD001`"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting business loads: {e}")
        return "❌ Error loading business loads. Please try again."

def get_progress_bar(percentage, width=10):
    """Create a text-based progress bar"""
    filled = int(width * percentage / 100)
    empty = width - filled
    return "▓" * filled + "░" * empty

def format_trip_planned_message(trip):
    """Format trip planned message with better styling"""
    # Build route string
    route = trip['origin']
    if trip.get('waypoints'):
        route += " → " + " → ".join(trip['waypoints'])
    route += " → " + trip['destination']
    
    # Build fuel stops string
    fuel_stops_str = ""
    if trip.get('fuel_stops'):
        for stop in trip['fuel_stops']:
            fuel_stops_str += f"   • {stop['city']} ({stop.get('estimated_fuel', 'N/A')})\n"
    else:
        fuel_stops_str = "   • No fuel stops planned\n"
    
    # Google Maps link
    maps_link = f"https://www.google.com/maps/dir/{trip['origin'].replace(' ', '+')}/{trip['destination'].replace(' ', '+')}"
    
    confidence = trip.get('confidence', 0)
    confidence_emoji = "✅" if confidence >= 0.75 else "⚠️" if confidence >= 0.5 else "❌"
    
    return (
        "✅ *Trip Planned Successfully!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 *Route:* {route}\n"
        f"🚛 *Truck:* {trip['truck_number']}\n"
        f"⚙️ *Condition:* {trip['condition']}\n"
        f"⛽ *Mileage:* {trip['mileage']} km/l\n\n"
        "📊 *Trip Details*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ *ETA:* {trip['eta_hours']} hours\n"
        f"📏 *Distance:* {trip['distance_km']} km\n"
        f"⛽ *Fuel Cost:* ₹{trip['fuel_cost']:,}\n"
        f"🛣️ *Toll Cost:* ₹{trip['toll_cost']:,}\n"
        f"💰 *Expected Profit:* ₹{trip['expected_profit']:,}\n"
        f"🎯 *Confidence:* {confidence} {confidence_emoji}\n\n"
        "⛽ *Fuel Stops*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{fuel_stops_str}\n"
        "👥 *Driver Information*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {trip['driver_name']}\n"
        f"📱 *Phone:* {trip['driver_phone']}\n\n"
        "🗺️ *Navigation*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{maps_link}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Trip has been assigned to driver. ✅"
    )

def format_unknown_command(message):
    """Format unknown command message with suggestions"""
    suggestions = []
    
    if any(word in message.lower() for word in ["trip", "from", "to", "delhi", "mumbai"]):
        suggestions.append("• Try: `Mumbai to Delhi`")
    
    if any(word in message.lower() for word in ["truck", "fleet", "status"]):
        suggestions.append("• Try: `FLEET STATUS`")
    
    if any(word in message.lower() for word in ["active", "ongoing", "trips"]):
        suggestions.append("• Try: `ACTIVE TRIPS`")
    
    if any(word in message.lower() for word in ["business", "load", "pending"]):
        suggestions.append("• Try: `BUSINESS LOADS`")
    
    suggestion_text = "\n".join(suggestions) if suggestions else "• Try: `HELP` for all commands"
    
    return (
        "🤖 *I didn't understand that command.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Did you mean:*\n\n"
        f"{suggestion_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "*Quick Examples:*\n"
        "• `Mumbai to Delhi` (Plan trip)\n"
        "• `FLEET STATUS` (Check trucks)\n"
        "• `ACTIVE TRIPS` (View shipments)\n"
        "• `BUSINESS LOADS` (View pending loads)\n"
        "• `HELP` (Show all commands)"
    )

def handle_message(message: str, phone_number: str = "+919999999999"):
    """Handle incoming WhatsApp messages based on user role"""
    logger.info(f"📱 Processing message from {phone_number}: '{message}'")
    
    message = message.strip()
    role = detect_user_role(phone_number)
    logger.info(f"👤 Detected user role: {role}")
    
    # ========== BUSINESS USER COMMANDS ==========
    if role == "business":
        return handle_business_response(message, phone_number)
    
    # ========== MANAGER COMMANDS ==========
    elif role == "manager":
        msg_lower = message.lower()
        
        # HI/HELLO command
        if msg_lower in ["hi", "hello", "hey"]:
            return format_manager_welcome()
        
        # HELP command
        elif msg_lower in ["help", "menu", "commands"]:
            return format_manager_help()
        
        # FLEET STATUS command
        elif "fleet" in msg_lower or ("trucks" in msg_lower and "status" in msg_lower):
            return format_fleet_status()
        
        # ACTIVE TRIPS command
        elif "active" in msg_lower and "trips" in msg_lower:
            return format_active_trips()
        
        # BUSINESS LOADS command
        elif "business" in msg_lower and "loads" in msg_lower:
            return format_pending_business_loads()
        
        # Handle load approval/rejection
        if "accept load" in msg_lower or "reject load" in msg_lower:
            return handle_manager_load_approval(message, phone_number)
        
        # TRIP PLANNING - More flexible patterns
        trip_match = extract_trip_details(message)
        if trip_match:
            origin, destination = trip_match
            logger.info(f"✅ Trip planning: {origin} → {destination}")
            
            # Plan trip with truck selection
            trip, error = plan_trip_with_truck(origin, destination)
            
            if error:
                logger.error(f"❌ Trip planning failed: {error}")
                return f"❌ {error}\n\nTry: `FLEET STATUS` to check available trucks."
            
            logger.info(f"✅ Trip planned successfully: {trip.get('id')}")
            
            # ========== ADDED: SEND BUSINESS NOTIFICATIONS ==========
            try:
                notifications = send_business_notifications(trip)
                logger.info(f"📤 Sent notifications to {len(notifications)} businesses")
            except Exception as e:
                logger.error(f"Failed to send business notifications: {e}")
            # ========== END ADDED CODE ==========
            
            return format_trip_planned_message(trip)
        
        # Unknown command
        return format_unknown_command(message)
    
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
        if re.search(r"^(1|start|accept|1️⃣)", msg_lower):
            if not driver_trip:
                return "❌ No trip assigned to you"
            
            success, msg = accept_trip(driver_trip['id'], phone_number)
            if not success:
                return f"❌ {msg}"
            
            # Start the trip
            start_trip(driver_trip['id'], driver_trip['origin'])
            return "✅ Trip started! Safe journey! 🚚\n\n*Commands:*\n📍 LOCATION - Update location\n📊 STATUS - Check trip status\n✅ ARRIVED - Mark as completed"
        
        # SHARE LOCATION / UPDATE LOCATION
        elif re.search(r"^(2|location|share|update|2️⃣)", msg_lower):
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
        elif re.search(r"^(3|delay|3️⃣)", msg_lower):
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
        elif re.search(r"arrived|reached|done|complete|finished", msg_lower):
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
        elif re.search(r"status|progress|check", msg_lower):
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
        # LOAD command - More flexible regex
        match = re.search(
            r"load\s+(\d+)\s*kg\s+(.+?)\s+(?:to|TO)\s+(.+)",
            message,
            re.IGNORECASE
        )
        
        if match:
            weight = int(match.group(1))
            pickup = match.group(2).strip()
            dropoff = match.group(3).strip()
            
            logger.info(f"📦 Load request: {weight}kg from {pickup} to {dropoff}")
            
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
    if re.search(r"^(hi|hello|start|help|menu|commands)$", message.lower()):
        if role == "manager":
            return format_manager_help()
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
        elif role == "business":
            return (
                "👋 *Hi Business Partner!*\n\n"
                "📋 *Available Commands:*\n\n"
                "• `YES` - Accept truck availability\n"
                "• `NO` - Decline truck availability\n"
                "• `CONFIRM <load_id>` - Confirm load booking\n"
                "• `REVISE <load_id>` - Request rate revision\n\n"
                "You'll receive notifications when trucks\n"
                "are passing near your location!"
            )
        else:
            return customer_load_request_message()
    
    # Unknown command for non-manager roles
    if role != "manager":
        return (
            "🤖 *I didn't understand that command.*\n\n"
            "Type `HELP` to see available commands."
        )
    
    # Manager unknown command should use the new format_unknown_command
    return format_unknown_command(message)

def test_webhook():
    """Test the webhook with sample messages"""
    print("\n" + "="*60)
    print("🧪 TESTING MANAGER COMMANDS")
    print("="*60)
    
    test_cases = [
        "hi",
        "HELP",
        "FLEET STATUS",
        "ACTIVE TRIPS",
        "BUSINESS LOADS",
        "START TRIP FROM Pune TO Agra",
        "start trip from pune to agra",
        "Start Trip From Pune To Agra", 
        "START TRIP FROM Pune to Agra",
        "start trip pune to agra",
        "trip pune to agra",
        "plan trip pune to agra",
        "from pune to agra",
        "Pune to Agra",
        "invalid command"
    ]
    
    for test in test_cases:
        print(f"\n{'─'*40}")
        print(f"📤 Input: {test}")
        result = handle_message(test, "+919999999999")
        print(f"📥 Response: {result[:200]}...")
    
    print("\n" + "="*60)
    print("🧪 TESTING DRIVER COMMANDS")
    print("="*60)
    print(handle_message("1", "+919876543210"))
    
    print("\n" + "="*60)
    print("🧪 TESTING CUSTOMER COMMANDS")
    print("="*60)
    print(handle_message("LOAD 500kg Mumbai to Pune", "+918888888888"))
    
    print("\n" + "="*60)
    print("🧪 TESTING BUSINESS COMMANDS")
    print("="*60)
    print(handle_message("YES", "+917777777777"))

if __name__ == "__main__":
    test_webhook()