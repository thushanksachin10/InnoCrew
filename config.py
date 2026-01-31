# config.py

MAX_LOAD_PERCENT = 90
MIN_FUEL_PERCENT = 25
AVG_SPEED_KMPH = 55

FUEL_PRICE_PER_LITER = 95  # ₹

CONFIDENCE_THRESHOLDS = {
    "auto_accept": 0.75,
    "needs_approval": 0.5
}

# API Configuration
# GraphHopper API (optional - leave empty to use free tier with limitations)
# Get your free API key at: https://www.graphhopper.com/
GRAPHHOPPER_API_KEY = "6e03cd3c-a401-49e1-821c-2d95ceb56721"  # Optional: Add your API key for higher rate limits

# If you have a GraphHopper API key, it will be used
# Otherwise, the system uses free public endpoints with rate limits
