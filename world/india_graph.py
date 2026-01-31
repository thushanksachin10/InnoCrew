# world/india_graph.py

import requests
from config import GRAPHHOPPER_API_KEY

def get_route(start, end):
    """
    Calculate route using GraphHopper Routing API
    Falls back to OSRM if GraphHopper fails
    
    Args:
        start: tuple (lat, lon)
        end: tuple (lat, lon)
    
    Returns:
        distance_km, duration_hr
    """
    # Try GraphHopper first
    try:
        url = "https://graphhopper.com/api/1/route"
        params = {
            "point": [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
            "vehicle": "truck",
            "locale": "en",
            "calc_points": "false",
            "points_encoded": "false"
        }
        
        # Add API key if available
        if GRAPHHOPPER_API_KEY:
            params["key"] = GRAPHHOPPER_API_KEY
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "paths" in data and len(data["paths"]) > 0:
            path = data["paths"][0]
            distance_km = path["distance"] / 1000
            duration_hr = path["time"] / (1000 * 3600)
            print(f"✓ GraphHopper route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
            return distance_km, duration_hr
    except Exception as e:
        print(f"GraphHopper routing failed: {e}")
    
    # Fallback to OSRM
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
        params = {"overview": "false"}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        route = data["routes"][0]
        distance_km = route["distance"] / 1000
        duration_hr = route["duration"] / 3600
        print(f"✓ OSRM route: {distance_km:.1f} km, {duration_hr:.1f} hrs")
        return distance_km, duration_hr
    except Exception as e:
        print(f"OSRM routing failed: {e}")
        raise Exception("Could not calculate route with any service")
