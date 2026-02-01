# whatsapp/templates.py

def business_opportunity_message(trip, business):
    """Message sent to businesses along the route"""
    return (
        f"🚚 *TRUCK PASSING NEAR YOU!*\n\n"
        f"📍 *Route:* {trip['origin']} → {trip['destination']}\n"
        f"📏 *Distance:* {trip['distance_km']} km\n"
        f"⏱️ *Timing:* Passing through {business.get('location', 'your area')} in 2-4 hours\n"
        f"🚛 *Truck:* {trip['truck_number']}\n"
        f"📦 *Available Capacity:* {trip.get('available_capacity_kg', 5000)} kg\n\n"
        f"*Do you have goods to send?*\n\n"
        f"Reply:\n"
        f"✅ YES - I want to send a load\n"
        f"❌ NO - Not interested\n\n"
        f"If YES, we'll ask for:\n"
        f"• Weight (kg)\n"
        f"• Pickup location\n"
        f"• Dropoff location\n\n"
        f"*Competitive rates for on-route loads!*"
    )

def load_rate_quote_message(load_details):
    """Rate quote sent to business customers"""
    return (
        f"📋 *RATE QUOTE*\n\n"
        f"*Load ID:* {load_details.get('id', 'N/A')}\n"
        f"*Weight:* {load_details['weight_kg']} kg\n"
        f"*Route:* {load_details['pickup']} → {load_details['dropoff']}\n\n"
        f"💰 *Total Cost:* ₹{load_details['weight_kg'] * load_details.get('rate_per_kg', 12):,}\n"
        f"📊 *Rate:* ₹{load_details.get('rate_per_kg', 12)}/kg\n\n"
        f"*Validity:* 24 hours\n"
        f"*Payment Terms:* COD/Credit\n\n"
        f"To confirm, reply:\n"
        f"✅ CONFIRM {load_details.get('id', 'N/A')}\n\n"
        f"Or request revision:\n"
        f"📝 REVISE {load_details.get('id', 'N/A')}"
    )

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

def truck_location_update_message(truck, location, eta, next_stop):
    """Message sent to customers about truck location"""
    return (
        f"🚚 *Truck Location Update*\n\n"
        f"📍 *Current Location:* {location}\n"
        f"🚛 *Truck Number:* {truck['number']}\n"
        f"📦 *Load Status:* {truck.get('load_status', 'In transit')}\n\n"
        f"⏱️ *ETA to {next_stop}:* {eta}\n"
        f"📏 *Distance Covered:* {truck.get('distance_covered_km', 0)} km\n"
        f"📊 *Journey Progress:* {truck.get('progress_percent', 0)}%\n\n"
        f"*Next Stop:* {next_stop}\n"
        f"*Driver Contact:* {truck.get('driver_contact', 'N/A')}\n\n"
        f"Reply HELP for assistance."
    )

def payment_confirmation_message(payment):
    """Message sent for payment confirmation"""
    return (
        f"💰 *Payment Confirmation*\n\n"
        f"*Transaction ID:* {payment['id']}\n"
        f"*Amount:* ₹{payment['amount']:,}\n"
        f"*Date:* {payment['date']}\n"
        f"*Method:* {payment['method']}\n\n"
        f"*Load Details:*\n"
        f"Weight: {payment['weight_kg']} kg\n"
        f"Route: {payment['pickup']} → {payment['dropoff']}\n\n"
        f"✅ Payment received successfully!\n"
        f"📧 Invoice will be emailed to {payment['email']}"
    )

def emergency_alert_message(trip, issue, location):
    """Emergency alert message"""
    return (
        f"🚨 *EMERGENCY ALERT*\n\n"
        f"*Truck:* {trip['truck_number']}\n"
        f"*Driver:* {trip['driver_name']}\n"
        f"*Contact:* {trip['driver_phone']}\n\n"
        f"*Issue:* {issue}\n"
        f"*Location:* {location}\n\n"
        f"*Trip Details:*\n"
        f"Route: {trip['origin']} → {trip['destination']}\n"
        f"ETA Remaining: {trip.get('eta_remaining', 'N/A')} hrs\n\n"
        f"*Immediate Action Required*\n"
        f"1. Contact driver\n"
        f"2. Arrange assistance\n"
        f"3. Update customer"
    )

def load_completion_message(trip, load):
    """Message sent when load is delivered"""
    return (
        f"✅ *Load Delivered Successfully!*\n\n"
        f"*Load ID:* {load['id']}\n"
        f"*Truck:* {trip['truck_number']}\n"
        f"*Route:* {load['pickup']} → {load['dropoff']}\n"
        f"*Weight:* {load['weight_kg']} kg\n\n"
        f"*Delivery Details:*\n"
        f"Time: {load['delivery_time']}\n"
        f"Receiver: {load['receiver_name']}\n"
        f"Signature: {load.get('signature', 'Collected')}\n\n"
        f"*Payment Status:* {load.get('payment_status', 'Pending')}\n"
        f"*Invoice:* {load.get('invoice_url', 'Will be sent shortly')}\n\n"
        f"Thank you for choosing our service!"
    )

def customer_feedback_request_message(trip):
    """Request feedback from customer"""
    return (
        f"📝 *We'd Love Your Feedback!*\n\n"
        f"*Trip Details:*\n"
        f"Truck: {trip['truck_number']}\n"
        f"Route: {trip['origin']} → {trip['destination']}\n"
        f"Date: {trip['date']}\n\n"
        f"*How was your experience?*\n\n"
        f"Reply with a rating (1-5):\n"
        f"5️⃣ Excellent\n"
        f"4️⃣ Good\n"
        f"3️⃣ Average\n"
        f"2️⃣ Poor\n"
        f"1️⃣ Very Poor\n\n"
        f"Or type your feedback directly.\n"
        f"Thank you for helping us improve!"
    )

def maintenance_reminder_message(truck, maintenance_type):
    """Maintenance reminder message"""
    return (
        f"🔧 *Maintenance Reminder*\n\n"
        f"*Truck:* {truck['number']}\n"
        f"*Type:* {maintenance_type}\n"
        f"*Last Service:* {truck['last_service']}\n"
        f"*Next Due:* {truck['next_service_due']}\n\n"
        f"*Details:*\n"
        f"Odometer: {truck['odometer']} km\n"
        f"Service Interval: {truck['service_interval_km']} km\n"
        f"Remaining: {truck['remaining_km']} km\n\n"
        f"*Reply:*\n"
        f"1️⃣ SCHEDULE SERVICE\n"
        f"2️⃣ ALREADY DONE\n"
        f"3️⃣ REMIND LATER"
    )

def business_partnership_offer(business_name, route_info):
    """Business partnership offer message"""
    return (
        f"🤝 *Business Partnership Opportunity*\n\n"
        f"*To:* {business_name}\n\n"
        f"We notice your business is located along our frequent truck routes:\n"
        f"• {route_info['routes']}\n\n"
        f"*Proposal:*\n"
        f"• Priority pickup/delivery slots\n"
        f"• Discounted rates (up to 15% off)\n"
        f"• Dedicated account manager\n"
        f"• Monthly consolidated billing\n\n"
        f"*Benefits for you:*\n"
        f"✓ Lower shipping costs\n"
        f"✓ Faster deliveries\n"
        f"✓ Reliable service\n"
        f"✓ Digital tracking\n\n"
        f"*Interested?* Reply:\n"
        f"✅ YES - Schedule a call\n"
        f"📋 INFO - Send more details\n"
        f"❌ NO - Not interested\n\n"
        f"Looking forward to collaborating!"
    )