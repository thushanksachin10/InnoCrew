# main.py
"""
Main entry point for AI Logistics Agent
"""

import uvicorn
from app import app
from logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("🚚 AI Logistics Agent - Starting up")
    logger.info("=" * 60)
    
    # Log configuration summary
    try:
        from config import (
            AVG_SPEED_KMPH, FUEL_PRICE_PER_LITER, 
            DRIVER_COST_PER_HOUR, LOG_LEVEL
        )
        logger.info(f"Configuration loaded:")
        logger.info(f"  • Average Speed: {AVG_SPEED_KMPH} km/h")
        logger.info(f"  • Fuel Price: ₹{FUEL_PRICE_PER_LITER}/L")
        logger.info(f"  • Driver Cost: ₹{DRIVER_COST_PER_HOUR}/hour")
        logger.info(f"  • Log Level: {LOG_LEVEL}")
    except ImportError as e:
        logger.error(f"Failed to load config: {e}")
    
    # Start the server
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None,
        access_log=False,
        reload=False  # Set to True for development
    )

if __name__ == "__main__":
    main()