# agent/agent_loop.py

from database.models import db
from world.route_eval import estimate_eta, estimate_fuel_cost, calculate_toll_cost
from world.india_graph import get_route
from agent.confidence import compute_confidence
from logging_config import get_logger

logger = get_logger(__name__)

def select_best_truck(origin, destination, distance_km):
    """Select the best available truck for the trip"""
    logger.info(f"Selecting best truck for {origin} → {destination} ({distance_km}km)")
    
    available_trucks = db.get_available_trucks(origin)
    logger.debug(f"Found {len(available_trucks)} available trucks")
    
    if not available_trucks:
        logger.warning(f"No available trucks found for origin: {origin}")
        return None

def plan_trip(distance_km, load_percent, mileage_kmpl):
    """Simple trip planning for backward compatibility"""
    eta = estimate_eta(distance_km)
    fuel_cost = estimate_fuel_cost(distance_km, mileage_kmpl)
    confidence = compute_confidence(load_percent, True, 0.9)  # Assume fuel_ok=True
    
    return eta, fuel_cost, confidence

def select_best_truck(origin, destination, distance_km):
    """Select the best available truck for the trip"""
    available_trucks = db.get_available_trucks(origin)
    
    if not available_trucks:
        return None
    
    # FIX: Use correct field names from database with .get() for safety
    scored_trucks = []
    for truck in available_trucks:
        score = 0
        
        # Condition score
        if truck.get('condition', 'Good') == 'Excellent':
            score += 1.2
        elif truck.get('condition', 'Good') == 'Good':
            score += 1.0
        else:
            score += 0.8
        
        # Mileage score (normalize)
        score += truck.get('mileage_kmpl', 5.0) / 10
        
        # Location bonus
        if truck.get('location', '').lower() == origin.lower():
            score += 0.5
        
        # Fuel level bonus (higher fuel = better)
        fuel_percent = truck.get('fuel_percent', 50)
        score += (fuel_percent / 100) * 0.3
        
        # Maintenance score (recent maintenance = better)
        last_maintenance = truck.get('last_maintenance', '2024-01-01')
        # Simple logic: if maintenance was within last 30 days, add bonus
        # In production, parse date and calculate
        score += 0.2  # Placeholder
        
        # Truck age penalty (older trucks slightly penalized)
        year = truck.get('year_of_manufacture', 2020)
        if year >= 2022:
            score += 0.1
        elif year >= 2020:
            score += 0.05
        
        scored_trucks.append((truck, score))
    
    # Sort by score and return best
    scored_trucks.sort(key=lambda x: x[1], reverse=True)
    return scored_trucks[0][0] if scored_trucks else None

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
    fuel_cost = estimate_fuel_cost(distance_km, truck.get('mileage_kmpl', 5.0))
    toll_cost = calculate_toll_cost(distance_km)
    
    # Calculate load percentage - FIXED: use .get() for safety
    current_load = truck.get('current_load_kg', 0)
    capacity = truck.get('capacity_kg', 10000)
    load_percent = (current_load / capacity) * 100 if capacity > 0 else 0
    
    # Compute confidence
    fuel_ok = truck.get('fuel_percent', 0) > 20  # Fuel OK if > 20%
    traffic_score = 0.9  # Simulated traffic score
    confidence = compute_confidence(load_percent, fuel_ok, traffic_score)
    
    # Calculate profit (estimate)
    # Assuming ₹30 per km as revenue
    revenue = distance_km * 30
    total_cost = fuel_cost + toll_cost
    profit = revenue - total_cost
    
    # Plan fuel stops
    fuel_stops = plan_fuel_stops(origin, destination, distance_km, truck.get('mileage_kmpl', 5.0))
    
    # Create trip data
    trip_data = {
        'origin': origin,
        'destination': destination,
        'waypoints': waypoints or [],
        'truck_id': truck['id'],
        'truck_number': truck.get('number', 'UNKNOWN'),
        'driver_phone': truck.get('driver_phone', ''),
        'driver_name': truck.get('driver_name', 'Unknown Driver'),
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
        'mileage': truck.get('mileage_kmpl', 5.0),
        'condition': truck.get('condition', 'Good'),
        'truck_fuel_percent': truck.get('fuel_percent', 80),  # ADDED: Track truck's current fuel
        'truck_capacity_kg': capacity,
        'truck_current_load_kg': current_load,
        'available_capacity_kg': capacity - current_load  # ADDED: Available capacity
    }
    
    # Save trip to database
    trip = db.create_trip(trip_data)
    
    # Mark truck as assigned - FIXED: use .get() for safety
    db.update_truck_status(truck.get('id'), 'assigned')
    
    # Update truck's current trip ID
    trucks = db.get_all_trucks()
    for t in trucks:
        if t['id'] == truck.get('id'):
            t['current_trip_id'] = trip['id']
            break
    db._save_json(db.trucks_file, trucks)
    
    return trip, None

def plan_fuel_stops(origin, destination, distance_km, mileage_kmpl):
    """Plan fuel stops along the route"""
    tank_capacity = 400  # liters (typical truck)
    range_km = tank_capacity * mileage_kmpl
    
    stops = []
    
    # Major cities along common routes (simplified)
    route_cities = {
        ('mumbai', 'delhi'): ['Surat', 'Vadodara', 'Udaipur', 'Jaipur'],
        ('mumbai', 'bangalore'): ['Pune', 'Kolhapur', 'Belgaum'],
        ('delhi', 'mumbai'): ['Jaipur', 'Udaipur', 'Vadodara', 'Surat'],
        ('bangalore', 'chennai'): ['Vellore'],
        ('pune', 'nagpur'): ['Aurangabad', 'Jalna'],
        ('delhi', 'chandigarh'): ['Panipat', 'Ambala'],
        ('chennai', 'bangalore'): ['Vellore'],
        ('kolkata', 'delhi'): ['Varanasi', 'Allahabad', 'Kanpur'],
        ('hyderabad', 'bangalore'): ['Kurnool', 'Anantapur'],
        ('ahmedabad', 'mumbai'): ['Vapi', 'Valsad', 'Surat'],
    }
    
    route_key = (origin.lower(), destination.lower())
    reverse_key = (destination.lower(), origin.lower())
    
    # Check both directions
    cities = route_cities.get(route_key, route_cities.get(reverse_key, []))
    
    if cities and distance_km > 300:  # Only plan stops for long routes
        # Calculate optimal stop intervals
        optimal_stop_distance = range_km * 0.6  # Refuel at 60% of range
        
        # Distribute stops along route
        num_stops = max(1, int(distance_km / optimal_stop_distance))
        
        if len(cities) >= num_stops:
            # Use actual cities from the route
            step = len(cities) // (num_stops + 1)
            for i in range(1, num_stops + 1):
                idx = min(i * step, len(cities) - 1)
                city = cities[idx]
                estimated_fuel = max(20, 100 - (i * (80 // (num_stops + 1))))
                stops.append({
                    'city': city,
                    'estimated_fuel': f"{estimated_fuel}%",
                    'reason': f"Refuel before reaching {destination}"
                })
        else:
            # Not enough cities in list, use generic stops
            for i in range(1, num_stops + 1):
                estimated_fuel = max(25, 100 - (i * (70 // (num_stops + 1))))
                stops.append({
                    'city': f'Stop {i}',
                    'estimated_fuel': f"{estimated_fuel}%",
                    'reason': f"Approximately {i * optimal_stop_distance:.0f}km from start"
                })
    
    return stops if stops else [{'city': 'Mid-route', 'estimated_fuel': '45%', 'reason': 'Regular refueling stop'}]

def accept_trip(trip_id, driver_phone):
    """Driver accepts the trip"""
    trip = db.get_trip_by_id(trip_id)
    
    if not trip:
        return False, "Trip not found"
    
    if trip.get('driver_phone') != driver_phone:
        return False, "Not authorized"
    
    db.update_trip_status(trip_id, 'accepted')
    
    # Update truck status - FIXED: use .get() for safety
    truck_id = trip.get('truck_id')
    if truck_id:
        db.update_truck_status(truck_id, 'in_transit')
    
    return True, "Trip accepted"

def start_trip(trip_id, location):
    """Driver starts the trip"""
    trip = db.get_trip_by_id(trip_id)
    if not trip:
        return False, "Trip not found"
    
    db.update_trip_status(trip_id, 'in_progress', location)
    
    # Update truck location
    truck_id = trip.get('truck_id')
    if truck_id:
        # Get truck and update its location
        trucks = db.get_all_trucks()
        for truck in trucks:
            if truck['id'] == truck_id:
                truck['location'] = location
                truck['last_location_update'] = "2024-01-31T12:00:00"  # Should be current timestamp
                break
        db._save_json(db.trucks_file, trucks)
    
    return True, f"Trip started from {location}"

def complete_trip(trip_id, location):
    """Driver completes the trip"""
    trip = db.get_trip_by_id(trip_id)
    if not trip:
        return False, "Trip not found"
    
    # Calculate actual profit (simplified)
    # In real system, you'd calculate based on actual fuel used, tolls, etc.
    actual_profit = trip.get('expected_profit', 0) * 0.95  # 5% variance
    
    # Update trip status
    db.update_trip_status(trip_id, 'completed', location)
    
    # Update truck status and location
    truck_id = trip.get('truck_id')
    if truck_id:
        db.update_truck_status(truck_id, 'available', location)
        
        # Reset truck's current load
        trucks = db.get_all_trucks()
        for truck in trucks:
            if truck['id'] == truck_id:
                truck['current_load_kg'] = 0
                truck['current_trip_id'] = None
                truck['location'] = location
                # Reduce fuel by estimated amount
                current_fuel = truck.get('fuel_percent', 80)
                distance = trip.get('distance_km', 0)
                mileage = truck.get('mileage_kmpl', 5.0)
                fuel_used = (distance / mileage) * 100 / 400  # 400L tank
                truck['fuel_percent'] = max(0, current_fuel - fuel_used)
                break
        db._save_json(db.trucks_file, trucks)
    
    # Update trip with actual completion data
    trips = db._load_json(db.trips_file)
    for t in trips:
        if t['id'] == trip_id:
            t['actual_profit'] = actual_profit
            t['end_time'] = "2024-01-31T18:00:00"  # Should be current timestamp
            t['progress_percent'] = 100
            break
    db._save_json(db.trips_file, trips)
    
    return True, f"Trip completed at {location}. Profit: ₹{actual_profit:,.0f}"

def update_trip_location(trip_id, location):
    """Update trip's current location"""
    trip = db.get_trip_by_id(trip_id)
    if not trip:
        return False, "Trip not found"
    
    # Calculate progress percentage
    # Simplified: assume linear progress
    # In real system, calculate based on route distance covered
    progress = trip.get('progress_percent', 0)
    if progress < 100:
        progress = min(progress + 10, 95)  # Increment by 10%
    
    db.update_trip_status(trip_id, 'in_progress', location)
    
    # Update trip progress
    trips = db._load_json(db.trips_file)
    for t in trips:
        if t['id'] == trip_id:
            t['current_location'] = location
            t['progress_percent'] = progress
            break
    db._save_json(db.trips_file, trips)
    
    return True, f"Location updated: {location} (Progress: {progress}%)"

def find_enroute_opportunities(truck_id):
    """Find additional load opportunities for a truck already on route"""
    truck = db.get_truck_by_id(truck_id)
    if not truck or truck.get('status') != 'in_transit':
        return []
    
    current_trip_id = truck.get('current_trip_id')
    if not current_trip_id:
        return []
    
    trip = db.get_trip_by_id(current_trip_id)
    if not trip:
        return []
    
    # Get available capacity
    available_capacity = trip.get('available_capacity_kg', 0)
    if available_capacity <= 0:
        return []
    
    # Get pending loads from database
    pending_loads = db.get_pending_loads()
    
    opportunities = []
    for load in pending_loads:
        # Check if load pickup is near the current route
        # Simplified: just check if pickup is a major city
        load_weight = load.get('weight_kg', 0)
        if load_weight <= available_capacity:
            # Calculate additional revenue (simplified)
            additional_revenue = load_weight * 0.5  # ₹0.5 per kg per 100km
            
            opportunities.append({
                'load_id': load.get('id'),
                'weight_kg': load_weight,
                'pickup': load.get('pickup'),
                'dropoff': load.get('dropoff'),
                'additional_revenue': additional_revenue,
                'detour_estimated': "1-2 hours",  # Simplified
                'profit_impact': f"+₹{additional_revenue:,.0f}"
            })
    
    return opportunities[:3]  # Return top 3 opportunities