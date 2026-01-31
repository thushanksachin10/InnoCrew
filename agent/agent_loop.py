# agent/agent_loop.py

from database.models import db
from world.route_eval import estimate_eta, estimate_fuel_cost, calculate_toll_cost
from world.india_graph import get_route
from agent.confidence import compute_confidence

def select_best_truck(origin, destination, distance_km):
    """Select the best available truck for the trip"""
    available_trucks = db.get_available_trucks(origin)
    
    if not available_trucks:
        return None
    
    # Score trucks based on:
    # 1. Condition (Good=1.0, Excellent=1.2, Fair=0.8)
    # 2. Mileage (higher is better)
    # 3. Proximity to origin
    
    scored_trucks = []
    for truck in available_trucks:
        score = 0
        
        # Condition score
        if truck['condition'] == 'Excellent':
            score += 1.2
        elif truck['condition'] == 'Good':
            score += 1.0
        else:
            score += 0.8
        
        # Mileage score (normalize)
        score += truck['mileage_kmpl'] / 10
        
        # Location bonus
        if truck['location'].lower() == origin.lower():
            score += 0.5
        
        scored_trucks.append((truck, score))
    
    # Sort by score and return best
    scored_trucks.sort(key=lambda x: x[1], reverse=True)
    return scored_trucks[0][0]

def plan_trip_with_truck(origin, destination, waypoints=None):
    """Plan a complete trip with truck selection"""
    
    # Get coordinates
    from whatsapp.webhook import geocode_city
    start_coords = geocode_city(origin)
    end_coords = geocode_city(destination)
    
    if not start_coords or not end_coords:
        return None, "Could not geocode cities"
    
    # Calculate route
    try:
        distance_km, duration_hr = get_route(start_coords, end_coords)
    except Exception as e:
        return None, f"Route calculation failed: {str(e)}"
    
    # Select best truck
    truck = select_best_truck(origin, destination, distance_km)
    
    if not truck:
        return None, "No trucks available"
    
    # Calculate costs
    eta_hours = estimate_eta(distance_km)
    fuel_cost = estimate_fuel_cost(distance_km, truck['mileage_kmpl'])
    toll_cost = calculate_toll_cost(distance_km)
    
    # Calculate load percentage
    load_percent = (truck['current_load_kg'] / truck['capacity_kg']) * 100
    
    # Compute confidence
    fuel_ok = True  # Assume truck has fuel
    traffic_score = 0.9  # Simulated traffic score
    confidence = compute_confidence(load_percent, fuel_ok, traffic_score)
    
    # Calculate profit (estimate)
    # Assuming ₹30 per km as revenue
    revenue = distance_km * 30
    total_cost = fuel_cost + toll_cost
    profit = revenue - total_cost
    
    # Plan fuel stops
    fuel_stops = plan_fuel_stops(origin, destination, distance_km, truck['mileage_kmpl'])
    
    # Create trip data
    trip_data = {
        'origin': origin,
        'destination': destination,
        'waypoints': waypoints or [],
        'truck_id': truck['id'],
        'truck_number': truck['number'],
        'driver_phone': truck['driver_phone'],
        'driver_name': truck['driver_name'],
        'distance_km': round(distance_km, 1),
        'eta_hours': round(eta_hours, 1),
        'fuel_cost': round(fuel_cost, 0),
        'toll_cost': round(toll_cost, 0),
        'total_cost': round(total_cost, 0),
        'expected_revenue': round(revenue, 0),
        'expected_profit': round(profit, 0),
        'confidence': confidence,
        'fuel_stops': fuel_stops,
        'load_percent': round(load_percent, 0),
        'mileage': truck['mileage_kmpl'],
        'condition': truck['condition']
    }
    
    # Save trip to database
    trip = db.create_trip(trip_data)
    
    # Mark truck as assigned
    db.update_truck_status(truck['id'], 'assigned')
    
    return trip, None

def plan_fuel_stops(origin, destination, distance_km, mileage_kmpl):
    """Plan fuel stops along the route"""
    tank_capacity = 400  # liters (typical truck)
    range_km = tank_capacity * mileage_kmpl
    
    stops = []
    remaining = distance_km
    current_fuel_percent = 100
    
    # Major cities along common routes (simplified)
    route_cities = {
        ('mumbai', 'delhi'): ['Surat', 'Vadodara', 'Udaipur', 'Jaipur'],
        ('mumbai', 'bangalore'): ['Pune', 'Kolhapur', 'Belgaum'],
        ('delhi', 'mumbai'): ['Jaipur', 'Udaipur', 'Vadodara', 'Surat'],
        ('bangalore', 'chennai'): ['Vellore'],
        ('pune', 'nagpur'): ['Aurangabad', 'Jalna'],
    }
    
    route_key = (origin.lower(), destination.lower())
    cities = route_cities.get(route_key, [])
    
    if cities:
        mid_point = len(cities) // 2
        for i, city in enumerate(cities):
            # Add fuel stops at strategic points
            if i == mid_point or (i > 0 and i % 2 == 0):
                fuel_percent = 100 - ((i + 1) / len(cities) * 60)
                stops.append({
                    'city': city,
                    'estimated_fuel': f"{int(fuel_percent)}%"
                })
    
    return stops if stops else [{'city': 'Mid-route', 'estimated_fuel': '45%'}]

def accept_trip(trip_id, driver_phone):
    """Driver accepts the trip"""
    trip = db.get_trip_by_id(trip_id)
    
    if not trip:
        return False, "Trip not found"
    
    if trip['driver_phone'] != driver_phone:
        return False, "Not authorized"
    
    db.update_trip_status(trip_id, 'accepted')
    db.update_truck_status(trip['truck_id'], 'in_transit')
    
    return True, "Trip accepted"

def start_trip(trip_id, location):
    """Driver starts the trip"""
    db.update_trip_status(trip_id, 'in_progress', location)
    return True
