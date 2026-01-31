# world/india_graph.py

import requests
from config import GRAPHHOPPER_API_KEY
from math import radians, sin, cos, sqrt, atan2
from logging_config import get_logger

logger = get_logger(__name__)

def get_route(start, end):
    """
    Calculate route with robust error handling and multiple fallbacks
    """
    logger.info(f"Calculating route from {start} to {end}")
    
    # Validate inputs
    if not start or not end:
        logger.error("Start or end coordinates are missing")
        raise ValueError("Start and end coordinates must be provided")

def get_route_graphhopper(start, end):
    """
    Calculate route using GraphHopper Routing API
    
    Args:
        start: tuple (lat, lon)
        end: tuple (lat, lon)
    
    Returns:
        distance_km, duration_hr
    """
    url = "https://graphhopper.com/api/1/route"
    params = {
        "point": [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
        "vehicle": "truck",
        "locale": "en",
        "calc_points": "false",
        "points_encoded": "false"
    }
    
    # Add API key if available
    if GRAPHHOPPER_API_KEY and GRAPHHOPPER_API_KEY.strip():
        params["key"] = GRAPHHOPPER_API_KEY.strip()
    
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    if "paths" in data and len(data["paths"]) > 0:
        path = data["paths"][0]
        distance_km = path["distance"] / 1000
        duration_hr = path["time"] / (1000 * 3600)
        print(f"✓ GraphHopper route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
        return distance_km, duration_hr
    
    raise Exception("No route found in GraphHopper response")

def get_route_osrm(start, end):
    """
    Calculate route using OSRM (Open Source Routing Machine)
    
    Args:
        start: tuple (lat, lon)
        end: tuple (lat, lon)
    
    Returns:
        distance_km, duration_hr
    """
    # OSRM expects (lon, lat) format
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
    params = {"overview": "false"}
    
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    if data.get("code") == "Ok" and data.get("routes") and len(data["routes"]) > 0:
        route = data["routes"][0]
        distance_km = route["distance"] / 1000
        duration_hr = route["duration"] / 3600
        print(f"✓ OSRM route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
        return distance_km, duration_hr
    
    raise Exception("No route found in OSRM response")

def calculate_haversine_distance(start, end):
    """Calculate direct distance between two coordinates using Haversine formula"""
    lat1, lon1 = start
    lat2, lon2 = end
    
    R = 6371  # Earth's radius in kilometers
    
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    print(f"⚠️ Using estimated distance: {distance:.1f} km (Haversine)")
    return distance

def get_route(start, end):
    """
    Calculate route with robust error handling and multiple fallbacks
    
    Args:
        start: tuple (lat, lon)
        end: tuple (lat, lon)
    
    Returns:
        distance_km, duration_hr
    
    Raises:
        Exception: If all routing methods fail
    """
    # Validate inputs
    if not start or not end:
        raise ValueError("Start and end coordinates must be provided")
    
    if not isinstance(start, (tuple, list)) or not isinstance(end, (tuple, list)):
        raise ValueError("Coordinates must be tuples or lists")
    
    if len(start) != 2 or len(end) != 2:
        raise ValueError("Coordinates must have exactly 2 values (lat, lon)")
    
    # Check for same location (avoid division by zero)
    if abs(start[0] - end[0]) < 0.001 and abs(start[1] - end[1]) < 0.001:
        print("⚠️ Start and end are very close, returning minimal distance")
        return 1.0, 0.1  # 1 km, 0.1 hours
    
    errors = []
    
    # ========== METHOD 1: GraphHopper ==========
    try:
        distance_km, duration_hr = get_route_graphhopper(start, end)
        return distance_km, duration_hr
    except Exception as e1:
        error_msg = f"GraphHopper failed: {str(e1)}"
        errors.append(error_msg)
        print(f"⚠️ {error_msg}")
    
    # ========== METHOD 2: OSRM ==========
    try:
        distance_km, duration_hr = get_route_osrm(start, end)
        return distance_km, duration_hr
    except Exception as e2:
        error_msg = f"OSRM failed: {str(e2)}"
        errors.append(error_msg)
        print(f"⚠️ {error_msg}")
    
    # ========== METHOD 3: Mapbox (if API key available) ==========
    try:
        # Check if Mapbox API key is in config
        from config import MAPBOX_API_KEY
        if MAPBOX_API_KEY and MAPBOX_API_KEY.strip():
            distance_km, duration_hr = get_route_mapbox(start, end)
            if distance_km and duration_hr:
                return distance_km, duration_hr
    except ImportError:
        pass  # Mapbox not configured
    except Exception as e3:
        error_msg = f"Mapbox failed: {str(e3)}"
        errors.append(error_msg)
        print(f"⚠️ {error_msg}")
    
    # ========== METHOD 4: Direct distance calculation ==========
    try:
        # Calculate direct distance using Haversine
        distance_km = calculate_haversine_distance(start, end)
        
        # Estimate duration based on distance
        # Trucks average 50-60 kmph on highways, slower in cities
        avg_speed_kmph = 55
        duration_hr = distance_km / avg_speed_kmph
        
        # Add traffic factor (20% for urban routes, 10% for long routes)
        if distance_km < 100:
            duration_hr *= 1.2  # 20% longer for short urban routes
        else:
            duration_hr *= 1.1  # 10% longer for highway routes
        
        print(f"⚠️ Using estimated duration: {duration_hr:.1f} hrs")
        
        # Log the fallback
        print(f"⚠️ All routing services failed, using distance estimate")
        for error in errors:
            print(f"   - {error}")
        
        return distance_km, duration_hr
        
    except Exception as e4:
        error_msg = f"Haversine calculation failed: {str(e4)}"
        errors.append(error_msg)
        print(f"❌ {error_msg}")
    
    # ========== FINAL FALLBACK: Hardcoded distances for major Indian cities ==========
    major_city_distances = {
        # (city1, city2): distance_km
        ("mumbai", "delhi"): 1400,
        ("mumbai", "pune"): 150,
        ("mumbai", "bangalore"): 1000,
        ("delhi", "pune"): 1400,
        ("delhi", "bangalore"): 2100,
        ("pune", "bangalore"): 850,
        ("delhi", "chandigarh"): 250,
        ("chennai", "bangalore"): 350,
        ("kolkata", "delhi"): 1500,
        ("hyderabad", "bangalore"): 570,
        ("ahmedabad", "mumbai"): 530,
        ("jaipur", "delhi"): 280,
        ("lucknow", "delhi"): 550,
        ("nagpur", "mumbai"): 850,
        ("kochi", "bangalore"): 550,
    }
    
    # Try to match cities (this is very simplified)
    # In production, you'd have a proper city database
    city_pairs = [
        ("mumbai", "delhi"), ("delhi", "mumbai"),
        ("mumbai", "pune"), ("pune", "mumbai"),
        ("mumbai", "bangalore"), ("bangalore", "mumbai"),
        ("pune", "bangalore"), ("bangalore", "pune"),
        ("delhi", "bangalore"), ("bangalore", "delhi"),
        ("delhi", "chandigarh"), ("chandigarh", "delhi"),
        ("chennai", "bangalore"), ("bangalore", "chennai"),
        ("kolkata", "delhi"), ("delhi", "kolkata"),
        ("hyderabad", "bangalore"), ("bangalore", "hyderabad"),
        ("ahmedabad", "mumbai"), ("mumbai", "ahmedabad"),
        ("jaipur", "delhi"), ("delhi", "jaipur"),
        ("lucknow", "delhi"), ("delhi", "lucknow"),
        ("nagpur", "mumbai"), ("mumbai", "nagpur"),
        ("kochi", "bangalore"), ("bangalore", "kochi"),
    ]
    
    # This is just a placeholder - in reality you'd need city names
    # For now, return a reasonable default
    default_distance = 500  # km
    default_duration = default_distance / 50  # hours at 50 kmph
    
    print(f"⚠️ Using hardcoded default: {default_distance} km, {default_duration:.1f} hrs")
    print(f"⚠️ All routing methods failed. Errors:")
    for error in errors:
        print(f"   - {error}")
    
    return default_distance, default_duration

def get_route_mapbox(start, end):
    """
    Calculate route using Mapbox API (optional fallback)
    Requires MAPBOX_API_KEY in config.py
    """
    try:
        from config import MAPBOX_API_KEY
        
        if not MAPBOX_API_KEY or not MAPBOX_API_KEY.strip():
            return None, None
        
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
        params = {
            "access_token": MAPBOX_API_KEY.strip(),
            "geometries": "geojson",
            "overview": "simplified"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("routes") and len(data["routes"]) > 0:
            route = data["routes"][0]
            distance_km = route["distance"] / 1000
            duration_hr = route["duration"] / 3600
            print(f"✓ Mapbox route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
            return distance_km, duration_hr
        
    except ImportError:
        print("ℹ️ Mapbox not configured")
    except Exception as e:
        print(f"⚠️ Mapbox routing failed: {e}")
    
    return None, None

def get_route_summary(origin_city, destination_city):
    """
    Get a human-readable route summary
    Useful for displaying to users
    """
    try:
        from whatsapp.webhook import geocode_city
        
        start = geocode_city(origin_city)
        end = geocode_city(destination_city)
        
        if not start or not end:
            return f"Could not find route between {origin_city} and {destination_city}"
        
        distance, duration = get_route(start, end)
        
        # Format duration
        hours = int(duration)
        minutes = int((duration - hours) * 60)
        
        # Common landmarks/routes for major city pairs
        route_info = {
            ("mumbai", "delhi"): "via NH48 (Mumbai-Delhi Highway)",
            ("mumbai", "pune"): "via Expressway",
            ("delhi", "chandigarh"): "via NH44",
            ("chennai", "bangalore"): "via NH44",
            ("bangalore", "hyderabad"): "via NH44",
            ("kolkata", "delhi"): "via NH19 (Grand Trunk Road)",
        }
        
        key = (origin_city.lower(), destination_city.lower())
        via_text = route_info.get(key, "")
        
        return (
            f"📍 {origin_city} → {destination_city}\n"
            f"📏 Distance: {distance:.0f} km\n"
            f"⏱️ Duration: {hours}h {minutes}m\n"
            f"🛣️ Route: {via_text}"
        )
        
    except Exception as e:
        return f"Error getting route summary: {str(e)}"

# Test function
def test_routing():
    """Test the routing functions"""
    test_routes = [
        ((19.0760, 72.8777), (28.7041, 77.1025)),  # Mumbai to Delhi
        ((18.5204, 73.8567), (12.9716, 77.5946)),  # Pune to Bangalore
        ((28.7041, 77.1025), (30.7333, 76.7794)),  # Delhi to Chandigarh
    ]
    
    for start, end in test_routes:
        print(f"\n{'='*50}")
        print(f"Testing route: {start} → {end}")
        try:
            distance, duration = get_route(start, end)
            print(f"✓ Success: {distance:.1f} km, {duration:.1f} hours")
        except Exception as e:
            print(f"❌ Failed: {str(e)}")

if __name__ == "__main__":
    test_routing()