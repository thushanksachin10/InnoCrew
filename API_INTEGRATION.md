# 🌐 API Integration Guide

This document explains how the AI Logistics Agent uses external APIs for geocoding and routing.

## Overview

The system uses a **multi-tier fallback approach** to ensure reliability:

```
GraphHopper (Primary) → Nominatim/OSRM (Fallback)
```

## 1. Geocoding (City → Coordinates)

### GraphHopper Geocoding API

**Primary service for converting city names to GPS coordinates**

**Endpoint:** `https://graphhopper.com/api/1/geocode`

**Example Request:**
```bash
GET https://graphhopper.com/api/1/geocode?q=Mumbai,India&limit=1&locale=en
```

**Example Response:**
```json
{
  "hits": [
    {
      "point": {
        "lat": 19.0759837,
        "lng": 72.8776559
      },
      "name": "Mumbai",
      "country": "India"
    }
  ]
}
```

**Features:**
- ✅ Worldwide coverage
- ✅ Supports landmarks, addresses, airports
- ✅ Fast response times
- ✅ Free tier: 500 requests/day (with API key)
- ✅ No API key: Basic rate limits

### Nominatim (Fallback)

**OpenStreetMap's geocoding service**

**Endpoint:** `https://nominatim.openstreetmap.org/search`

**Example Request:**
```bash
GET https://nominatim.openstreetmap.org/search?q=Pune,India&format=json&limit=1
```

**Example Response:**
```json
[
  {
    "lat": "18.5203303",
    "lon": "73.8567437",
    "display_name": "Pune, Maharashtra, India"
  }
]
```

**Features:**
- ✅ Free and open source
- ✅ No API key required
- ✅ Good coverage
- ⚠️ Rate limited (1 request/second)

## 2. Routing (Distance & Duration)

### GraphHopper Routing API

**Primary service for truck routing**

**Endpoint:** `https://graphhopper.com/api/1/route`

**Example Request:**
```bash
GET https://graphhopper.com/api/1/route
  ?point=19.076,72.877  # Mumbai
  &point=28.704,77.102  # Delhi
  &vehicle=truck
  &locale=en
```

**Example Response:**
```json
{
  "paths": [
    {
      "distance": 1400567.8,  // meters
      "time": 90720000,       // milliseconds
      "points": {...}
    }
  ]
}
```

**Features:**
- ✅ **Truck-specific routing** (considers height, weight restrictions)
- ✅ Traffic-aware (with API key)
- ✅ Toll road information
- ✅ Turn-by-turn navigation
- ✅ Multiple route alternatives
- ✅ Free tier: 500 requests/day

**Conversion:**
```python
distance_km = distance_meters / 1000
duration_hours = time_ms / (1000 * 3600)
```

### OSRM (Fallback)

**Open Source Routing Machine**

**Endpoint:** `http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}`

**Example Request:**
```bash
GET http://router.project-osrm.org/route/v1/driving/72.877,19.076;77.102,28.704?overview=false
```

**Example Response:**
```json
{
  "routes": [
    {
      "distance": 1400567.8,  // meters
      "duration": 90720.0     // seconds
    }
  ]
}
```

**Features:**
- ✅ Free and open source
- ✅ Fast response
- ✅ No API key required
- ⚠️ Car routing (not truck-specific)
- ⚠️ No traffic data

## 3. How the System Uses APIs

### Geocoding Flow

```python
def geocode_city(city_name):
    # 1. Try GraphHopper
    try:
        response = requests.get(
            "https://graphhopper.com/api/1/geocode",
            params={"q": city_name + ", India", "limit": 1}
        )
        if response.ok:
            return (lat, lon)
    except:
        pass
    
    # 2. Fallback to Nominatim
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city_name + ", India", "format": "json"}
        )
        if response.ok:
            return (lat, lon)
    except:
        pass
    
    # 3. Return None if both fail
    return None
```

### Routing Flow

```python
def get_route(start_coords, end_coords):
    # 1. Try GraphHopper (truck routing)
    try:
        response = requests.get(
            "https://graphhopper.com/api/1/route",
            params={
                "point": [f"{start[0]},{start[1]}", f"{end[0]},{end[1]}"],
                "vehicle": "truck"
            }
        )
        if response.ok:
            return (distance_km, duration_hr)
    except:
        pass
    
    # 2. Fallback to OSRM
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
        response = requests.get(url)
        if response.ok:
            return (distance_km, duration_hr)
    except:
        pass
    
    # 3. Raise error if both fail
    raise Exception("Routing failed")
```

## 4. Getting API Keys

### GraphHopper API Key (Recommended)

**Free Tier:**
- 500 requests/day
- All features included
- Credit card NOT required

**Steps:**
1. Go to https://www.graphhopper.com/
2. Click "Get Started Free"
3. Sign up with email
4. Go to Dashboard → API Keys
5. Copy your API key
6. Add to `config.py`:
   ```python
   GRAPHHOPPER_API_KEY = "your-key-here"
   ```

**Paid Tiers:**
- Starter: $49/month (10,000 requests/day)
- Business: $299/month (100,000 requests/day)
- Enterprise: Custom pricing

### Why Use GraphHopper?

**Truck-Specific Features:**
- 🚚 Considers vehicle height, weight, width
- 🚫 Avoids restricted roads, low bridges
- 📏 Accurate truck distances (different from car routes)
- ⏱️ Better ETA for heavy vehicles
- 🛣️ Toll road information

**Example Difference:**
```
Car route:  Mumbai → Delhi via highway = 1,410 km
Truck route: Mumbai → Delhi avoiding restrictions = 1,450 km
```

## 5. Rate Limits & Best Practices

### Without API Key

**GraphHopper (Free Public Endpoint):**
- Rate limit: ~5 requests/minute
- Use for: Testing, low-volume

**Nominatim:**
- Rate limit: 1 request/second
- Must include User-Agent header
- Use for: Fallback only

**OSRM:**
- Rate limit: Fair use policy
- Use for: Fallback routing

### With GraphHopper API Key (Free Tier)

- Rate limit: 500 requests/day
- Burst: 5 requests/second
- Use for: Production with moderate traffic

### Optimization Tips

1. **Cache Results:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def geocode_city(city_name):
       # Caches coordinates for frequently used cities
   ```

2. **Batch Requests:** If planning multiple trips, cache city coordinates

3. **Error Handling:** Always have fallback logic

4. **Retry Logic:**
   ```python
   import time
   
   for attempt in range(3):
       try:
           return get_route(start, end)
       except:
           if attempt < 2:
               time.sleep(1)  # Wait before retry
   ```

## 6. Alternative APIs (Future)

### Google Maps API
- **Pro:** Best coverage, traffic data
- **Con:** Paid only ($5 per 1000 requests)

### Mapbox
- **Pro:** 100,000 free requests/month
- **Con:** Requires credit card

### HERE Maps
- **Pro:** 250,000 free transactions/month
- **Con:** Complex pricing

### TomTom
- **Pro:** Good truck routing
- **Con:** Limited free tier

## 7. Testing APIs

### Test Geocoding
```bash
# GraphHopper
curl "https://graphhopper.com/api/1/geocode?q=Mumbai,India&limit=1"

# Nominatim
curl "https://nominatim.openstreetmap.org/search?q=Mumbai,India&format=json&limit=1"
```

### Test Routing
```bash
# GraphHopper
curl "https://graphhopper.com/api/1/route?point=19.076,72.877&point=28.704,77.102&vehicle=truck"

# OSRM
curl "http://router.project-osrm.org/route/v1/driving/72.877,19.076;77.102,28.704?overview=false"
```

## 8. Troubleshooting

### Error: "Rate limit exceeded"
**Solution:** 
- Add GraphHopper API key
- Implement caching
- Add delays between requests

### Error: "City not found"
**Solution:**
- Check spelling
- Try with state: "Vashi, Maharashtra"
- Use nearby major city

### Error: "Route calculation failed"
**Solution:**
- Check internet connection
- Verify coordinates are valid
- Check if route is too long (>2000 km might timeout)

### Error: "403 Forbidden"
**Solution:**
- GraphHopper: Check API key is valid
- Nominatim: Add User-Agent header
- OSRM: Check fair use policy

## 9. Cost Estimation

### For 1000 Trips/Month

**Without API Key (Free):**
- GraphHopper: May hit rate limits
- Nominatim: Should work but slow
- OSRM: Should work
- **Cost:** $0

**With GraphHopper Free Tier:**
- 500 requests/day = 15,000/month
- Enough for 7,500 trips (geocode + route)
- **Cost:** $0

**With GraphHopper Starter:**
- 10,000 requests/day = 300,000/month
- Enough for 150,000 trips
- **Cost:** $49/month

## 10. Summary

| Feature | GraphHopper | Nominatim | OSRM |
|---------|-------------|-----------|------|
| Geocoding | ✅ Best | ✅ Good | ❌ No |
| Routing | ✅ Best (truck) | ❌ No | ✅ Good (car) |
| API Key | Optional | No | No |
| Free Tier | 500/day | 1/second | Fair use |
| Traffic | ✅ Yes (with key) | ❌ No | ❌ No |
| Truck Routes | ✅ Yes | ❌ No | ❌ No |

**Recommendation:** 
- Start without API key for testing
- Add GraphHopper API key for production
- System automatically handles fallbacks

---

**Last Updated:** January 31, 2026  
**API Versions:** GraphHopper v1, Nominatim v1, OSRM v1
