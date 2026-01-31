# config.py
import os

# ========== OPERATIONAL CONSTANTS ==========
MAX_LOAD_PERCENT = 90  # Maximum safe load percentage
MIN_FUEL_PERCENT = 25  # Minimum fuel percentage before refueling recommended
AVG_SPEED_KMPH = 55    # Average truck speed in km/h
DRIVER_COST_PER_HOUR = 300  # ₹ per hour for driver salary
OPERATING_COST_PER_KM = 15  # ₹ per km for maintenance, insurance, etc.

FUEL_PRICE_PER_LITER = 95  # ₹ Current diesel price in India
TOLL_COST_PER_KM = 1.5     # ₹ Average toll cost per km for trucks
REVENUE_PER_KM = 30        # ₹ Average revenue per km

# ========== BUSINESS LOGIC CONSTANTS ==========
CONFIDENCE_THRESHOLDS = {
    "auto_accept": 0.75,   # Auto-accept opportunities above this confidence
    "needs_approval": 0.5, # Need manager approval below this
    "reject": 0.3          # Auto-reject below this
}

PROFIT_MARGIN_TARGETS = {
    "minimum": 0.15,       # 15% minimum profit margin
    "target": 0.25,        # 25% target profit margin
    "excellent": 0.35      # 35% excellent profit margin
}

# ========== TIME & SCHEDULE CONSTANTS ==========
DRIVER_MAX_HOURS = 12      # Maximum driving hours per day (India regulation)
DRIVER_REST_HOURS = 1      # Mandatory rest after 4 hours
BREAK_INTERVAL_HOURS = 4   # Break required every 4 hours
MIN_LOADING_TIME_HOURS = 2 # Minimum time for loading/unloading

# ========== API CONFIGURATION ==========
# GraphHopper API (optional - leave empty to use free tier with limitations)
# Get your free API key at: https://www.graphhopper.com/
GRAPHHOPPER_API_KEY = "6e03cd3c-a401-49e1-821c-2d95ceb56721"  # Optional

# Mapbox API (optional - for additional routing fallback)
# Get your free API key at: https://www.mapbox.com/
MAPBOX_API_KEY = ""  # Optional - add if available

# ========== SYSTEM CONSTANTS ==========
MAX_RETRY_ATTEMPTS = 3     # Maximum retry attempts for API calls
REQUEST_TIMEOUT_SECONDS = 15  # Timeout for external API calls
CACHE_DURATION_MINUTES = 30   # How long to cache route calculations
LOG_LEVEL = "INFO"         # DEBUG, INFO, WARNING, ERROR

# ========== DATABASE CONSTANTS ==========
DATABASE_PATH = "data/data.db"
BACKUP_INTERVAL_HOURS = 24
MAX_TRIPS_HISTORY = 1000   # Maximum trips to keep in history
MAX_LOGS_RETENTION_DAYS = 30

# ========== WHATSAPP/TEMPLATE CONSTANTS ==========
MESSAGE_MAX_LENGTH = 1600  # WhatsApp message character limit
UPDATE_INTERVAL_MINUTES = 30  # How often to send location updates
NOTIFICATION_HOURS_BEFORE = [24, 12, 2]  # Notify X hours before delivery

# ========== ADAPTIVE ROUTING CONSTANTS ==========
MAX_DETOUR_PERCENT = 20    # Maximum 20% detour for additional pickups
MIN_ADDITIONAL_PROFIT = 5000  # Minimum ₹5000 additional profit for detour
RE_ROUTE_CHECK_INTERVAL_KM = 100  # Check for re-routing every 100km

# ========== TRUCK CONSTANTS ==========
TRUCK_TYPES = {
    "20ft Container": {"capacity_kg": 10000, "avg_mileage": 5.5},
    "14ft Truck": {"capacity_kg": 7000, "avg_mileage": 6.2},
    "22ft Container": {"capacity_kg": 12000, "avg_mileage": 4.8},
    "18ft Truck": {"capacity_kg": 9000, "avg_mileage": 5.8}
}

DEFAULT_TRUCK_CONDITIONS = ["Excellent", "Good", "Fair", "Poor"]
MAINTENANCE_INTERVAL_KM = 10000  # Maintenance every 10,000 km

# ========== VALIDATION ==========
def validate_config():
    """Validate all configuration values"""
    errors = []
    
    # Speed validation
    if AVG_SPEED_KMPH <= 0 or AVG_SPEED_KMPH > 120:
        errors.append("AVG_SPEED_KMPH must be between 1 and 120")
    
    # Price validation
    if FUEL_PRICE_PER_LITER <= 0 or FUEL_PRICE_PER_LITER > 200:
        errors.append("FUEL_PRICE_PER_LITER must be between 1 and 200")
    
    if DRIVER_COST_PER_HOUR <= 0 or DRIVER_COST_PER_HOUR > 1000:
        errors.append("DRIVER_COST_PER_HOUR must be between 1 and 1000")
    
    # Threshold validation
    if not 0 <= CONFIDENCE_THRESHOLDS['auto_accept'] <= 1:
        errors.append("auto_accept threshold must be between 0 and 1")
    
    if not 0 <= CONFIDENCE_THRESHOLDS['needs_approval'] <= 1:
        errors.append("needs_approval threshold must be between 0 and 1")
    
    if not 0 <= CONFIDENCE_THRESHOLDS['reject'] <= 1:
        errors.append("reject threshold must be between 0 and 1")
    
    # Ensure thresholds are in correct order
    if CONFIDENCE_THRESHOLDS['auto_accept'] <= CONFIDENCE_THRESHOLDS['needs_approval']:
        errors.append("auto_accept threshold must be greater than needs_approval")
    
    if CONFIDENCE_THRESHOLDS['needs_approval'] <= CONFIDENCE_THRESHOLDS['reject']:
        errors.append("needs_approval threshold must be greater than reject")
    
    # Profit margin validation
    for key, value in PROFIT_MARGIN_TARGETS.items():
        if not 0 <= value <= 1:
            errors.append(f"{key} profit margin must be between 0 and 1")
    
    # Driver hours validation (India regulation)
    if DRIVER_MAX_HOURS > 12:
        errors.append("DRIVER_MAX_HOURS cannot exceed 12 (India regulation)")
    
    if DRIVER_MAX_HOURS < 4:
        errors.append("DRIVER_MAX_HOURS must be at least 4")
    
    # Time interval validation
    if BREAK_INTERVAL_HOURS < 1:
        errors.append("BREAK_INTERVAL_HOURS must be at least 1")
    
    # API key format validation (if provided)
    if GRAPHHOPPER_API_KEY and not isinstance(GRAPHHOPPER_API_KEY, str):
        errors.append("GRAPHHOPPER_API_KEY must be a string")
    
    if MAPBOX_API_KEY and not isinstance(MAPBOX_API_KEY, str):
        errors.append("MAPBOX_API_KEY must be a string")
    
    # Adaptive routing validation
    if MAX_DETOUR_PERCENT < 0 or MAX_DETOUR_PERCENT > 100:
        errors.append("MAX_DETOUR_PERCENT must be between 0 and 100")
    
    if MIN_ADDITIONAL_PROFIT < 0:
        errors.append("MIN_ADDITIONAL_PROFIT cannot be negative")
    
    # Database validation
    if MAX_TRIPS_HISTORY < 100:
        errors.append("MAX_TRIPS_HISTORY must be at least 100")
    
    if MAX_LOGS_RETENTION_DAYS < 1:
        errors.append("MAX_LOGS_RETENTION_DAYS must be at least 1")
    
    if errors:
        error_msg = "Configuration errors:\n" + "\n".join(f"  • {error}" for error in errors)
        raise ValueError(error_msg)
    
    print("✓ Configuration validated successfully")

def get_effective_fuel_price():
    """Get fuel price with potential adjustments"""
    # Could be extended to fetch live prices from API
    return FUEL_PRICE_PER_LITER

def calculate_minimum_rate(distance_km, truck_type="20ft Container"):
    """Calculate minimum rate for a trip based on costs"""
    truck_info = TRUCK_TYPES.get(truck_type, TRUCK_TYPES["20ft Container"])
    avg_mileage = truck_info["avg_mileage"]
    
    # Calculate costs
    fuel_cost = (distance_km / avg_mileage) * get_effective_fuel_price()
    driver_cost = (distance_km / AVG_SPEED_KMPH) * DRIVER_COST_PER_HOUR
    operating_cost = distance_km * OPERATING_COST_PER_KM
    toll_cost = distance_km * TOLL_COST_PER_KM
    
    total_cost = fuel_cost + driver_cost + operating_cost + toll_cost
    
    # Add minimum profit margin
    minimum_rate = total_cost * (1 + PROFIT_MARGIN_TARGETS["minimum"])
    
    return {
        "distance_km": distance_km,
        "fuel_cost": round(fuel_cost),
        "driver_cost": round(driver_cost),
        "operating_cost": round(operating_cost),
        "toll_cost": round(toll_cost),
        "total_cost": round(total_cost),
        "minimum_rate": round(minimum_rate),
        "target_rate": round(total_cost * (1 + PROFIT_MARGIN_TARGETS["target"])),
        "breakdown": {
            "fuel": f"{fuel_cost/total_cost*100:.1f}%",
            "driver": f"{driver_cost/total_cost*100:.1f}%",
            "operations": f"{operating_cost/total_cost*100:.1f}%",
            "tolls": f"{toll_cost/total_cost*100:.1f}%"
        }
    }

# ========== INITIALIZATION ==========
# Call validation when config is imported
validate_config()

# Export all constants
__all__ = [
    'MAX_LOAD_PERCENT', 'MIN_FUEL_PERCENT', 'AVG_SPEED_KMPH', 
    'DRIVER_COST_PER_HOUR', 'OPERATING_COST_PER_KM', 'FUEL_PRICE_PER_LITER',
    'TOLL_COST_PER_KM', 'REVENUE_PER_KM', 'CONFIDENCE_THRESHOLDS',
    'PROFIT_MARGIN_TARGETS', 'DRIVER_MAX_HOURS', 'DRIVER_REST_HOURS',
    'BREAK_INTERVAL_HOURS', 'MIN_LOADING_TIME_HOURS', 'GRAPHHOPPER_API_KEY',
    'MAPBOX_API_KEY', 'MAX_RETRY_ATTEMPTS', 'REQUEST_TIMEOUT_SECONDS',
    'CACHE_DURATION_MINUTES', 'LOG_LEVEL', 'DATABASE_PATH',
    'BACKUP_INTERVAL_HOURS', 'MAX_TRIPS_HISTORY', 'MAX_LOGS_RETENTION_DAYS',
    'MESSAGE_MAX_LENGTH', 'UPDATE_INTERVAL_MINUTES', 'NOTIFICATION_HOURS_BEFORE',
    'MAX_DETOUR_PERCENT', 'MIN_ADDITIONAL_PROFIT', 'RE_ROUTE_CHECK_INTERVAL_KM',
    'TRUCK_TYPES', 'DEFAULT_TRUCK_CONDITIONS', 'MAINTENANCE_INTERVAL_KM',
    'validate_config', 'get_effective_fuel_price', 'calculate_minimum_rate'
]