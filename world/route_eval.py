# world/route_eval.py

from config import FUEL_PRICE_PER_LITER, AVG_SPEED_KMPH
from logging_config import get_logger

logger = get_logger(__name__)

def estimate_fuel_cost(distance_km, mileage):
    """Estimate fuel cost for a trip"""
    logger.debug(f"Estimating fuel cost for {distance_km}km with {mileage} kmpl mileage")
    
    fuel_liters = distance_km / mileage
    cost = fuel_liters * FUEL_PRICE_PER_LITER
    
    logger.debug(f"Estimated fuel: {fuel_liters:.1f}L, cost: ₹{cost:.0f}")
    return cost

def estimate_fuel(distance_km, mileage):
    return distance_km / mileage

def estimate_fuel_cost(distance_km, mileage):
    return estimate_fuel(distance_km, mileage) * FUEL_PRICE_PER_LITER

def estimate_eta(distance_km):
    return distance_km / AVG_SPEED_KMPH

def calculate_toll_cost(distance_km):
    """
    Estimate toll costs for Indian highways
    Average: ₹1.5 per km for trucks
    """
    # Major highways have tolls every 50-100 km
    # Average toll: ₹75-150 per booth
    # Simplified calculation: ₹1.5 per km
    return distance_km * 1.5
