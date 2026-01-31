# whatsapp/templates.py

def manager_trip_planned_message(trip):
    """Message sent to manager when trip is planned"""
    
    # Build route string
    route = trip['origin']
    if trip.get('waypoints'):
        route += " → " + " → ".join(trip['waypoints'])
    route += " → " + trip['destination']
    
    # Build fuel stops string
    fuel_stops_str = ""
    for stop in trip['fuel_stops']:
        fuel_stops_str += f"• {stop['city']} ({stop['estimated_fuel']})\n"
    
    # Google Maps link
    waypoints_param = ""
    if trip.get('waypoints'):
        waypoints_param = "/" + "/".join(trip['waypoints'])
    
    maps_link = f"https://www.google.com/maps/dir/{trip['origin']}{waypoints_param}/{trip['destination']}"
    maps_link = maps_link.replace(' ', '+')
    
    return (
        f"✅ *Trip Planned*\n\n"
        f"📍 *Route:* {route}\n"
        f"🚚 *Truck:* {trip['truck_number']}\n"
        f"⚙️ *Condition:* {trip['condition']}\n"
        f"⛽ *Mileage:* {trip['mileage']} km/l\n\n"
        f"⏱️ *ETA:* {trip['eta_hours']} hrs\n"
        f"⛽ *Fuel Cost:* ₹{trip['fuel_cost']:,}\n"
        f"🛣️ *Toll Cost:* ₹{trip['toll_cost']:,}\n"
        f"💰 *Expected Profit:* ₹{trip['expected_profit']:,}\n"
        f"🎯 *Confidence:* {trip['confidence']} {'✅' if trip['confidence'] >= 0.75 else '⚠️'}\n\n"
        f"🗺️ *Navigation Map:*\n{maps_link}\n\n"
        f"⛽ *Fuel Stops Planned:*\n{fuel_stops_str}\n"
        f"👤 *Driver:* {trip['driver_name']}\n"
        f"📱 *Driver Phone:* {trip['driver_phone']}\n\n"
        f"Trip has been assigned to driver."
    )

def driver_trip_assigned_message(trip):
    """Message sent to driver when trip is assigned"""
    
    # Build route string
    route = trip['origin']
    if trip.get('waypoints'):
        route += " → " + " → ".join(trip['waypoints'])
    route += " → " + trip['destination']
    
    # Build fuel stops string
    fuel_stops_str = ""
    for stop in trip['fuel_stops']:
        fuel_stops_str += f"• {stop['city']} ({stop['estimated_fuel']})\n"
    
    # Google Maps link
    waypoints_param = ""
    if trip.get('waypoints'):
        waypoints_param = "/" + "/".join(trip['waypoints'])
    
    maps_link = f"https://www.google.com/maps/dir/{trip['origin']}{waypoints_param}/{trip['destination']}"
    maps_link = maps_link.replace(' ', '+')
    
    return (
        f"🚚 *Trip Assigned*\n\n"
        f"📍 *Route:* {route}\n"
        f"⏱️ *ETA:* {trip['eta_hours']} hrs\n"
        f"📏 *Distance:* {trip['distance_km']} km\n\n"
        f"🗺️ *Navigation Map:*\n{maps_link}\n\n"
        f"⛽ *Fuel Stops Planned:*\n{fuel_stops_str}\n"
        f"*Reply:*\n"
        f"1️⃣ START\n"
        f"2️⃣ SHARE LOCATION\n"
        f"3️⃣ DELAY"
    )

def customer_load_request_message():
    """Help message for customers"""
    return (
        "📦 *Load Booking Service*\n\n"
        "To request a load pickup:\n\n"
        "*Format:*\n"
        "`LOAD <weight>kg <pickup> to <dropoff>`\n\n"
        "*Examples:*\n"
        "• `LOAD 500kg Mumbai to Pune`\n"
        "• `LOAD 1200kg Delhi to Jaipur`\n"
        "• `LOAD 300kg Bangalore to Chennai`\n\n"
        "You'll receive:\n"
        "✅ Load confirmation\n"
        "✅ Truck assignment\n"
        "✅ Live tracking link\n"
        "✅ ETA updates"
    )

def enroute_load_offer_message(trip, load):
    """Message sent when there's a truck passing near pickup location"""
    
    capacity_left_percent = 100 - trip['load_percent']
    
    return (
        f"📦 *Truck Passing Nearby!*\n\n"
        f"📍 *Route:* {trip['origin']} → {trip['destination']}\n"
        f"📦 *Capacity Left:* {capacity_left_percent}%\n"
        f"⏰ *Pickup Window:* Next 2-4 hours\n\n"
        f"*Your Load:*\n"
        f"Weight: {load['weight_kg']} kg\n"
        f"Pickup: {load['pickup']}\n"
        f"Dropoff: {load['dropoff']}\n\n"
        f"*Reply:*\n"
        f"1️⃣ ACCEPT\n"
        f"2️⃣ REJECT"
    )

def trip_update_message(trip, current_location, eta_remaining):
    """Message sent during trip for updates"""
    return (
        f"🚚 *Trip Update*\n\n"
        f"📍 *Current Location:* {current_location}\n"
        f"🎯 *Destination:* {trip['destination']}\n"
        f"⏱️ *ETA Remaining:* {eta_remaining} hrs\n\n"
        f"Status: On track ✅"
    )
