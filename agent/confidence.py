# agent/confidence.py
from logging_config import get_logger

logger = get_logger(__name__)

def compute_confidence(load_percent, fuel_ok, traffic_score):
    """Compute confidence score for a trip"""
    logger.debug(f"Computing confidence - Load: {load_percent}%, Fuel OK: {fuel_ok}, Traffic: {traffic_score}")
    
    score = 1.0

    if load_percent > 85:
        score *= 0.8
        logger.warning(f"High load ({load_percent}%) reducing confidence")
    
    if not fuel_ok:
        score *= 0.6
        logger.warning("Low fuel reducing confidence")
    
    score *= traffic_score
    final_score = round(score, 2)
    
    logger.debug(f"Final confidence score: {final_score}")
    return final_score

def compute_confidence(load_percent, fuel_ok, traffic_score):
    score = 1.0

    if load_percent > 85:
        score *= 0.8
    if not fuel_ok:
        score *= 0.6

    score *= traffic_score
    return round(score, 2)
