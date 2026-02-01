# whatsapp/business_notifications.py

import re
from logging_config import get_logger
from database.models import db
from whatsapp.templates import business_opportunity_message, load_rate_quote_message

logger = get_logger(__name__)

def get_businesses_along_route(origin, destination, route_cities=None):
    """Find businesses along the planned route"""
    logger.info(f"Finding businesses along route: {origin} → {destination}")
    
    # Load all users
    users = db._load_json(db.users_file)
    
    # Filter for businesses
    businesses = [u for u in users if u.get('role') == 'business']
    
    # Major cities between common routes
    route_city_mapping = {
        ('mumbai', 'delhi'): ['Surat', 'Vadodara', 'Udaipur', 'Jaipur'],
        ('mumbai', 'bangalore'): ['Pune', 'Kolhapur', 'Belgaum'],
        ('delhi', 'mumbai'): ['Jaipur', 'Udaipur', 'Vadodara', 'Surat'],
        ('bangalore', 'chennai'): ['Vellore', 'Kanchipuram'],
        ('pune', 'nagpur'): ['Aurangabad', 'Jalna'],
        ('delhi', 'chandigarh'): ['Panipat', 'Ambala'],
        ('kolkata', 'delhi'): ['Varanasi', 'Allahabad', 'Kanpur'],
        ('hyderabad', 'bangalore'): ['Kurnool', 'Anantapur'],
        ('ahmedabad', 'mumbai'): ['Vapi', 'Valsad', 'Surat'],
        ('mumbai', 'goa'): ['Panvel', 'Kolhapur', 'Belgaum'],
        ('delhi', 'kolkata'): ['Kanpur', 'Varanasi', 'Patna'],
        ('chennai', 'hyderabad'): ['Vijayawada', 'Nellore'],
    }
    
    # Get cities along this route
    route_key = (origin.lower(), destination.lower())
    reverse_key = (destination.lower(), origin.lower())
    
    cities_on_route = []
    if route_key in route_city_mapping:
        cities_on_route = route_city_mapping[route_key]
    elif reverse_key in route_city_mapping:
        cities_on_route = route_city_mapping[reverse_key]
    
    # Also include origin and destination cities
    cities_on_route.extend([origin, destination])
    
    # Find businesses in these cities
    relevant_businesses = []
    for business in businesses:
        business_city = business.get('location', '').lower()
        for city in cities_on_route:
            if city.lower() in business_city or business_city in city.lower():
                relevant_businesses.append(business)
                break
    
    logger.info(f"Found {len(relevant_businesses)} businesses along route")
    return relevant_businesses

def send_business_notifications(trip_data):
    """Send notifications to businesses along the route"""
    origin = trip_data['origin']
    destination = trip_data['destination']
    trip_id = trip_data['id']
    
    businesses = get_businesses_along_route(origin, destination)
    
    notifications_sent = []
    for business in businesses:
        # Create notification message
        message = business_opportunity_message(trip_data, business)
        
        # Store notification for later sending
        notification = {
            'trip_id': trip_id,
            'business_phone': business['phone'],
            'business_name': business['name'],
            'business_location': business.get('location'),
            'business_type': business.get('type'),
            'message': message,
            'status': 'sent',
            'timestamp': '2024-01-31T12:00:00'
        }
        
        notifications_sent.append(notification)
        logger.info(f"📤 Business notification sent to {business['name']} ({business['phone']})")
    
    return notifications_sent

def handle_business_response(message, phone_number):
    """Handle business responses to notifications"""
    logger.info(f"Processing business response from {phone_number}: {message}")
    
    # Check if message is a load request
    load_match = re.search(
        r"load\s+(\d+)\s*kg\s+(.+?)\s+(?:to|TO)\s+(.+)",
        message,
        re.IGNORECASE
    )
    
    if load_match:
        weight = int(load_match.group(1))
        pickup = load_match.group(2).strip()
        dropoff = load_match.group(3).strip()
        
        logger.info(f"📦 Business load request: {weight}kg from {pickup} to {dropoff}")
        
        # Create load request with business flag
        load_data = {
            'weight_kg': weight,
            'pickup': pickup,
            'dropoff': dropoff,
            'customer_phone': phone_number,
            'customer_type': 'business',
            'status': 'pending_manager_approval',
            'rate_per_kg': 15,  # Higher rate for businesses
            'is_opportunistic': True  # Flag for on-route loads
        }
        
        load = db.create_load_request(load_data)
        
        # Find manager phone
        users = db._load_json(db.users_file)
        manager = next((u for u in users if u.get('role') == 'manager'), None)
        
        if manager:
            manager_message = (
                f"📦 *NEW BUSINESS LOAD REQUEST*\n\n"
                f"*From:* {load_data['pickup']}\n"
                f"*To:* {load_data['dropoff']}\n"
                f"*Weight:* {load_data['weight_kg']} kg\n"
                f"*Customer:* Business ({phone_number})\n"
                f"*Rate:* ₹{load_data['rate_per_kg']}/kg\n\n"
                f"*Load ID:* {load.get('id', 'N/A')}\n\n"
                f"*Reply:*\n"
                f"✅ ACCEPT LOAD {load.get('id', 'N/A')}\n"
                f"❌ REJECT LOAD {load.get('id', 'N/A')}"
            )
            
            # Store for manager
            logger.info(f"📤 Manager notification created for load {load.get('id')}")
        
        return (
            f"📋 *Load Request Received*\n\n"
            f"*Load ID:* {load.get('id', 'N/A')}\n"
            f"*Weight:* {weight} kg\n"
            f"*Route:* {pickup} → {dropoff}\n"
            f"*Estimated Rate:* ₹{weight * 15:,}\n\n"
            "Your request has been sent to our manager for approval.\n"
            "You'll receive a rate confirmation shortly."
        )
    
    # Handle YES/NO responses to opportunity
    elif message.lower() in ['yes', 'y', 'interested']:
        return (
            "📦 *Great! You're interested in sending a load.*\n\n"
            "Please reply with your load details:\n"
            "`LOAD <weight>kg <pickup> to <dropoff>`\n\n"
            "*Example:*\n"
            "`LOAD 500kg Vadodara to Jaipur`\n\n"
            "We'll provide you with a rate quote."
        )
    
    elif message.lower() in ['no', 'n', 'not interested']:
        return "Thanks for letting us know! We'll notify you about future opportunities."
    
    return "I didn't understand. Reply 'YES' if interested in sending a load, or 'NO' if not."

def handle_manager_load_approval(message, phone_number):
    """Handle manager's approval/rejection of business loads"""
    logger.info(f"Processing manager load decision: {message}")
    
    # Check for ACCEPT/REJECT commands
    accept_match = re.search(r"accept\s+load\s+(\w+)", message, re.IGNORECASE)
    reject_match = re.search(r"reject\s+load\s+(\w+)", message, re.IGNORECASE)
    
    if accept_match:
        load_id = accept_match.group(1).upper()
        
        # Find the load
        loads = db._load_json(db.loads_file)
        load = next((l for l in loads if l.get('id') == load_id), None)
        
        if not load:
            return f"❌ Load {load_id} not found"
        
        # Find suitable trip for this load
        active_trips = db.get_active_trips()
        suitable_trip = None
        
        for trip in active_trips:
            # Check if load pickup/dropoff aligns with trip route
            trip_route_lower = f"{trip['origin'].lower()} {trip['destination'].lower()}"
            if (load['pickup'].lower() in trip_route_lower or 
                load['dropoff'].lower() in trip_route_lower):
                
                # Check capacity
                available_capacity = trip.get('available_capacity_kg', 0)
                if available_capacity >= load['weight_kg']:
                    suitable_trip = trip
                    break
        
        if suitable_trip:
            # Update load status
            load['status'] = 'approved'
            load['trip_id'] = suitable_trip['id']
            load['assigned_truck'] = suitable_trip['truck_number']
            load['driver_phone'] = suitable_trip['driver_phone']
            
            # Update trip with waypoint
            if load['pickup'] != suitable_trip['origin']:
                # Add as waypoint if not origin
                trips = db._load_json(db.trips_file)
                for t in trips:
                    if t['id'] == suitable_trip['id']:
                        if 'waypoints' not in t:
                            t['waypoints'] = []
                        if load['pickup'] not in t['waypoints']:
                            t['waypoints'].append(load['pickup'])
                        if load['dropoff'] not in t['waypoints']:
                            t['waypoints'].append(load['dropoff'])
                        t['available_capacity_kg'] = t.get('available_capacity_kg', 10000) - load['weight_kg']
                        break
                db._save_json(db.trips_file, trips)
            
            # Send rate quote to business customer
            rate = load['weight_kg'] * load.get('rate_per_kg', 12)
            
            # Save load updates
            db._save_json(db.loads_file, loads)
            
            # Send notification to business
            business_message = (
                f"✅ *LOAD APPROVED!*\n\n"
                f"*Load ID:* {load_id}\n"
                f"*Weight:* {load['weight_kg']} kg\n"
                f"*Route:* {load['pickup']} → {load['dropoff']}\n"
                f"*Assigned Truck:* {suitable_trip['truck_number']}\n"
                f"*Driver:* {suitable_trip['driver_name']}\n"
                f"📱 *Driver Contact:* {suitable_trip['driver_phone']}\n\n"
                f"💰 *Final Rate:* ₹{rate:,}\n\n"
                f"*Pickup Instructions:*\n"
                f"Truck will arrive at {load['pickup']} in approximately 2-4 hours.\n"
                f"Please have your goods ready for loading.\n\n"
                f"*Tracking ID:* TRACK{load_id}"
            )
            
            # Send notification to driver
            driver_message = (
                f"📦 *ADDITIONAL LOAD ASSIGNED*\n\n"
                f"*Load ID:* {load_id}\n"
                f"*Pickup:* {load['pickup']}\n"
                f"*Dropoff:* {load['dropoff']}\n"
                f"*Weight:* {load['weight_kg']} kg\n"
                f"*Customer:* {load.get('customer_phone', 'Business')}\n\n"
                f"*Additional Revenue:* ₹{rate:,}\n\n"
                f"Please collect the load during your trip.\n"
                f"Updated route will be sent shortly."
            )
            
            return (
                f"✅ *Load {load_id} Approved!*\n\n"
                f"*Assigned to:* {suitable_trip['truck_number']}\n"
                f"*Driver:* {suitable_trip['driver_name']}\n"
                f"*Additional Revenue:* ₹{rate:,}\n\n"
                f"Rate quote sent to business customer.\n"
                f"Driver notified about additional pickup."
            )
        else:
            return f"❌ No suitable trip found for load {load_id}"
    
    elif reject_match:
        load_id = reject_match.group(1).upper()
        
        # Update load status
        loads = db._load_json(db.loads_file)
        for l in loads:
            if l.get('id') == load_id:
                l['status'] = 'rejected'
                break
        db._save_json(db.loads_file, loads)
        
        return f"❌ Load {load_id} has been rejected."
    
    return "Please use: ACCEPT LOAD <load_id> or REJECT LOAD <load_id>"