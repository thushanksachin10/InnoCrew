# logging_config.py - Simplified version

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging(log_level="INFO", log_to_file=True, log_to_console=True):
    """
    Simplified logging setup without symlinks
    """
    # Convert string log level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Clear any existing handlers
    logging.root.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Create handlers
    handlers = []
    
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(level)
        handlers.append(console_handler)
    
    if log_to_file:
        # Simple log file - overwrite each time
        log_file = LOG_DIR / "app.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set external library logging levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('geopy').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Get config to check log level
    try:
        from config import LOG_LEVEL
        # Update level if config has different setting
        config_level = getattr(logging, LOG_LEVEL.upper(), level)
        if config_level != level:
            for handler in handlers:
                handler.setLevel(config_level)
            logging.getLogger().setLevel(config_level)
    except ImportError:
        pass  # config may not be available
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Level: {logging.getLevelName(level)}")
    if log_to_file:
        logger.info(f"Log file: {log_file}")
    
    return logger

def get_logger(name):
    """
    Get a named logger instance
    """
    return logging.getLogger(name)

def log_exception(logger, exception, context=""):
    """
    Log an exception with context
    """
    logger.error(f"{context}: {type(exception).__name__}: {str(exception)}", exc_info=True)

def log_performance(logger, func_name, start_time, end_time):
    """
    Log function performance
    """
    duration = (end_time - start_time).total_seconds()
    logger.debug(f"Function '{func_name}' took {duration:.3f} seconds")

class LoggingMiddleware:
    """Middleware for HTTP request logging"""
    
    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Log request
            path = scope.get("path", "")
            method = scope.get("method", "")
            self.logger.info(f"HTTP {method} {path}")
            
            # Create a custom send to log response
            async def send_wrapper(message):
                if message.get("type") == "http.response.start":
                    status = message.get("status", 0)
                    self.logger.info(f"HTTP Response: {status} for {method} {path}")
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# Export
__all__ = ['setup_logging', 'get_logger', 'log_exception', 'log_performance', 'LoggingMiddleware']