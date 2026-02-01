# world/india_graph.py - INTEGRATE AWS

import requests
from config import USE_AWS_AS_PRIMARY, FALLBACK_TO_OSRM, FALLBACK_TO_HAVERSINE, GRAPHHOPPER_API_KEY, MAPBOX_API_KEY
from math import radians, sin, cos, sqrt, atan2
from logging_config import get_logger

logger = get_logger(__name__)

# Import AWS service
try:
    from world.aws_routing import get_aws_route, aws_calculator
    AWS_AVAILABLE = aws_calculator.initialized
    if AWS_AVAILABLE:
        logger.info("✅ AWS Location Service available")
    else:
        logger.warning("⚠️ AWS Location Service not initialized")
except ImportError:
    logger.warning("AWS routing module not available")
    AWS_AVAILABLE = False

def get_route(start, end):
    """Main route calculation with AWS as primary"""
    logger.info(f"Calculating route: {start} → {end}")
    
    # Validate inputs
    if not start or not end:
        raise ValueError("Start and end coordinates required")
    
    if not isinstance(start, (tuple, list)) or not isinstance(end, (tuple, list)):
        raise ValueError("Coordinates must be tuples or lists")
    
    if len(start) != 2 or len(end) != 2:
        raise ValueError("Coordinates must have exactly 2 values (lat, lon)")
    
    # Check for same location
    if abs(start[0] - end[0]) < 0.001 and abs(start[1] - end[1]) < 0.001:
        logger.warning("Same location detected")
        return 1.0, 0.1
    
    errors = []
    
    # ========== METHOD 1: AWS Location Service ==========
    if USE_AWS_AS_PRIMARY and AWS_AVAILABLE:
        try:
            distance_km, duration_hr = get_aws_route(start, end)
            if distance_km and duration_hr:
                logger.info(f"✓ AWS route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
                return distance_km, duration_hr
        except Exception as e:
            errors.append(f"AWS: {str(e)}")
            logger.warning(f"⚠️ AWS failed: {e}")
    
    # ========== METHOD 2: GraphHopper ==========
    try:
        distance_km, duration_hr = get_route_graphhopper(start, end)
        if distance_km and duration_hr:
            logger.info(f"✓ GraphHopper route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
            return distance_km, duration_hr
    except Exception as e:
        errors.append(f"GraphHopper: {str(e)}")
        logger.warning(f"⚠️ GraphHopper failed: {e}")
    
    # ========== METHOD 3: OSRM (Free Open Source) ==========
    if FALLBACK_TO_OSRM:
        try:
            distance_km, duration_hr = get_route_osrm(start, end)
            if distance_km and duration_hr:
                logger.info(f"✓ OSRM route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
                return distance_km, duration_hr
        except Exception as e:
            errors.append(f"OSRM: {str(e)}")
            logger.warning(f"⚠️ OSRM failed: {e}")
    
    # ========== METHOD 4: Mapbox ==========
    try:
        if MAPBOX_API_KEY and MAPBOX_API_KEY.strip():
            distance_km, duration_hr = get_route_mapbox(start, end)
            if distance_km and duration_hr:
                logger.info(f"✓ Mapbox route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
                return distance_km, duration_hr
    except Exception as e:
        errors.append(f"Mapbox: {str(e)}")
        logger.warning(f"⚠️ Mapbox failed: {e}")
    
    # ========== METHOD 5: Haversine (Direct distance) ==========
    if FALLBACK_TO_HAVERSINE:
        try:
            distance_km = calculate_haversine_distance(start, end)
            avg_speed = 55  # km/h for trucks
            duration_hr = distance_km / avg_speed
            
            # Add traffic factor
            if distance_km < 100:
                duration_hr *= 1.2  # 20% longer for short urban routes
            else:
                duration_hr *= 1.1  # 10% longer for highway routes
            
            logger.warning(f"⚠️ Using estimated: {distance_km:.1f} km, {duration_hr:.1f} hrs")
            return distance_km, duration_hr
            
        except Exception as e:
            errors.append(f"Haversine: {str(e)}")
            logger.error(f"❌ Haversine failed: {e}")
    
    # ========== FINAL FALLBACK: Hardcoded distances ==========
    default_distance = 500  # km
    default_duration = default_distance / 50  # hours at 50 kmph
    
    logger.error("All routing methods failed, using hardcoded default")
    for error in errors:
        logger.error(f"  - {error}")
    
    return default_distance, default_duration

def get_route_graphhopper(start, end):
    """
    Calculate route using GraphHopper Routing API with better error handling
    
    Args:
        start: tuple (lat, lon)
        end: tuple (lat, lon)
    
    Returns:
        distance_km, duration_hr
    """
    try:
        url = "https://graphhopper.com/api/1/route"
        params = {
            "point": [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
            "vehicle": "car",  # Changed from "truck" to "car" for free tier
            "locale": "en",
            "calc_points": "false",
            "points_encoded": "false"
        }
        
        # Add API key if available
        if GRAPHHOPPER_API_KEY and GRAPHHOPPER_API_KEY.strip():
            params["key"] = GRAPHHOPPER_API_KEY.strip()
        else:
            logger.warning("No GraphHopper API key configured, skipping...")
            raise Exception("No GraphHopper API key")
        
        response = requests.get(url, params=params, timeout=10)
        
        # Check for specific errors
        if response.status_code == 401:
            logger.warning("GraphHopper: Invalid API key (401)")
            raise Exception("Invalid GraphHopper API key")
        elif response.status_code == 400:
            # Try without vehicle parameter for free tier
            logger.warning("GraphHopper: Bad request, trying without vehicle parameter...")
            params.pop("vehicle", None)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
        
        data = response.json()
        
        if "paths" in data and len(data["paths"]) > 0:
            path = data["paths"][0]
            distance_km = path["distance"] / 1000
            duration_hr = path["time"] / (1000 * 3600)
            return distance_km, duration_hr
        else:
            logger.warning(f"GraphHopper: No route found in response: {data}")
            raise Exception("No route found in GraphHopper response")
            
    except Exception as e:
        logger.warning(f"GraphHopper routing failed: {e}")
        raise

def get_route_osrm(start, end):
    """
    Calculate route using OSRM (Open Source Routing Machine)
    
    Args:
        start: tuple (lat, lon)
        end: tuple (lat, lon)
    
    Returns:
        distance_km, duration_hr
    """
    try:
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
            return distance_km, duration_hr
        
        raise Exception("No route found in OSRM response")
        
    except Exception as e:
        logger.warning(f"OSRM routing failed: {e}")
        raise

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
    logger.info(f"Calculated Haversine distance: {distance:.1f} km")
    return distance

def get_route_mapbox(start, end):
    """
    Calculate route using Mapbox API (optional fallback)
    Requires MAPBOX_API_KEY in config.py
    """
    try:
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
            return distance_km, duration_hr
        
    except ImportError:
        logger.info("Mapbox not configured")
    except Exception as e:
        logger.warning(f"Mapbox routing failed: {e}")
    
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