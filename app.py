# app.py

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime

from whatsapp.webhook import handle_message
from logging_config import setup_logging, get_logger, LoggingMiddleware
from database.models import db

# Setup logging FIRST - before anything else
try:
    setup_logging()
except Exception as e:
    # If logging setup fails, at least print to console
    print(f"⚠️ Logging setup failed: {e}")
    print("⚠️ Continuing with basic logging...")
    import logging
    logging.basicConfig(level=logging.INFO)

logger = get_logger(__name__)

app = FastAPI(
    title="AI Logistics Agent",
    version="2.0",
    description="Adaptive logistics system with AI-powered decision making",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware, logger=logger)

# Session storage for phone numbers (in production, use Redis or database)
user_sessions = {}

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 AI Logistics Agent starting up...")
    logger.info(f"Service: AI Logistics Agent v2.0")
    logger.info(f"Environment: {'development' if __name__ == '__main__' else 'production'}")
    
    # Initialize database if needed
    try:
        # Force re-initialization to ensure all tables exist
        db._init_files()
        logger.info("✓ Database initialized")
        
        # Log some stats - handle missing methods gracefully
        try:
            trucks = db.get_all_trucks()
            logger.info(f"✓ Loaded {len(trucks)} trucks")
        except AttributeError as e:
            logger.warning(f"get_all_trucks() method not available: {e}")
            trucks = []
        except Exception as e:
            logger.warning(f"Could not load trucks: {e}")
            trucks = []
        
        try:
            # Note: _load_json is a private method, use getter methods if available
            # Try to use public API first, fallback to private method
            trips = []
            if hasattr(db, 'get_all_trips'):
                trips = db.get_all_trips()
            else:
                trips = db._load_json(db.trips_file)
            logger.info(f"✓ Loaded {len(trips)} trips")
        except Exception as e:
            logger.warning(f"Could not load trips: {e}")
            trips = []
        
        try:
            loads = []
            if hasattr(db, 'get_all_loads'):
                loads = db.get_all_loads()
            else:
                loads = db._load_json(db.loads_file)
            logger.info(f"✓ Loaded {len(loads)} loads")
        except Exception as e:
            logger.warning(f"Could not load loads: {e}")
            loads = []
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 AI Logistics Agent shutting down...")

@app.post("/message")
async def message(message: str = Form(...), phone: str = Form("+919999999999")):
    """Handle incoming messages"""
    logger.info(f"📱 Received message from {phone}: {message[:50]}...")
    
    try:
        reply = handle_message(message, phone)
        logger.info(f"📤 Sent reply to {phone}: {reply[:50]}...")
        return {"reply": reply}
    except Exception as e:
        logger.error(f"❌ Error handling message from {phone}: {str(e)}", exc_info=True)
        return {"reply": "❌ An error occurred. Please try again."}

@app.get("/")
async def ui():
    """Serve the chat interface"""
    logger.info("🖥️ Serving UI")
    
    html_path = Path("ui/index.html")
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    
    logger.warning("UI file not found at ui/index.html")
    return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Logistics Agent</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                }
                .container {
                    background: #f5f5f5;
                    border-radius: 10px;
                    padding: 30px;
                    margin-top: 20px;
                }
                h1 { color: #333; }
                .endpoint {
                    background: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                    text-align: left;
                    border-left: 4px solid #4CAF50;
                }
                code {
                    background: #e0e0e0;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <h1>🚚 AI Logistics Agent API</h1>
            <p>Version 2.0 - Adaptive Logistics System</p>
            
            <div class="container">
                <h2>API Endpoints</h2>
                
                <div class="endpoint">
                    <strong>POST /message</strong>
                    <p>Send a message to the agent</p>
                    <p><code>message=START TRIP FROM Mumbai TO Delhi&phone=+919999999999</code></p>
                </div>
                
                <div class="endpoint">
                    <strong>GET /health</strong>
                    <p>Health check endpoint</p>
                </div>
                
                <div class="endpoint">
                    <strong>GET /logs</strong>
                    <p>View recent application logs</p>
                </div>
                
                <div class="endpoint">
                    <strong>GET /metrics</strong>
                    <p>System metrics and statistics</p>
                </div>
                
                <div class="endpoint">
                    <strong>GET /docs</strong>
                    <p>Interactive API documentation (Swagger UI)</p>
                </div>
                
                <div class="endpoint">
                    <strong>GET /fleet</strong>
                    <p>Get fleet information</p>
                </div>
                
                <div class="endpoint">
                    <strong>GET /trips</strong>
                    <p>Get trip information</p>
                </div>
            </div>
            
            <div style="margin-top: 30px;">
                <p>For the full chat interface, ensure <code>ui/index.html</code> exists.</p>
                <p>Or use the API endpoints directly.</p>
            </div>
        </body>
        </html>
    """)

@app.get("/health")
async def health():
    """Health check endpoint"""
    logger.debug("🩺 Health check requested")
    
    # Basic health checks
    health_status = {
        "status": "healthy",
        "service": "AI Logistics Agent v2.0",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "checks": {}
    }
    
    try:
        # Check database
        trucks = db.get_all_trucks()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "trucks_count": len(trucks)
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    try:
        # Check external services (simplified)
        import requests
        # Quick check if GraphHopper is reachable
        requests.get("https://graphhopper.com/api/1/geocode?q=Mumbai&limit=1", timeout=3)
        health_status["checks"]["external_apis"] = {
            "status": "healthy"
        }
    except Exception as e:
        health_status["checks"]["external_apis"] = {
            "status": "degraded",
            "error": str(e)[:100]
        }
        health_status["status"] = "degraded"
    
    return JSONResponse(content=health_status)

@app.get("/logs")
async def get_logs(limit: int = 100, level: str = None):
    """View recent logs (for debugging)"""
    logger.info("📝 Logs endpoint accessed")
    
    try:
        # Since we simplified logging_config.py, we now use app.log
        log_file = Path("logs/app.log")
        if not log_file.exists():
            # Check for any log file
            log_dir = Path("logs")
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                log_file = log_files[0]  # Get first log file
            else:
                return {"error": "No log files found"}
        
        lines = log_file.read_text(encoding='utf-8').splitlines()
        
        # Filter by level if specified
        if level:
            lines = [line for line in lines if f" - {level.upper()} - " in line]
        
        recent = lines[-limit:] if len(lines) > limit else lines
        
        return {
            "log_file": str(log_file),
            "total_lines": len(lines),
            "filtered_lines": len(recent),
            "filter_level": level,
            "logs": recent
        }
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
        return {"error": "Could not read logs", "details": str(e)}

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    logger.debug("📊 Metrics endpoint accessed")
    
    try:
        trucks = db.get_all_trucks()
        
        # Load trips and loads with fallback
        trips = []
        if hasattr(db, 'get_all_trips'):
            trips = db.get_all_trips()
        else:
            trips = db._load_json(db.trips_file)
        
        loads = []
        if hasattr(db, 'get_all_loads'):
            loads = db.get_all_loads()
        else:
            loads = db._load_json(db.loads_file)
        
        # Calculate some business metrics
        active_trips = [t for t in trips if t.get('status') in ['pending', 'accepted', 'in_progress']]
        completed_trips = [t for t in trips if t.get('status') == 'completed']
        
        total_expected_profit = sum(t.get('expected_profit', 0) for t in completed_trips)
        avg_profit_per_trip = total_expected_profit / len(completed_trips) if completed_trips else 0
        
        return {
            "trucks": {
                "total": len(trucks),
                "available": len([t for t in trucks if t.get('status') == 'available']),
                "assigned": len([t for t in trucks if t.get('status') == 'assigned']),
                "in_transit": len([t for t in trucks if t.get('status') == 'in_transit'])
            },
            "trips": {
                "total": len(trips),
                "active": len(active_trips),
                "completed": len(completed_trips),
                "pending": len([t for t in trips if t.get('status') == 'pending']),
                "average_profit": round(avg_profit_per_trip, 2),
                "total_expected_profit": round(total_expected_profit, 2)
            },
            "loads": {
                "total": len(loads),
                "pending": len([l for l in loads if l.get('status') == 'pending']),
                "assigned": len([l for l in loads if l.get('status') == 'assigned'])
            },
            "system": {
                "uptime": "N/A",
                "log_files": len(list(Path("logs").glob("*.log"))) if Path("logs").exists() else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return {"error": "Could not fetch metrics", "details": str(e)}

@app.get("/fleet")
async def get_fleet(status: str = None):
    """Get fleet information"""
    logger.info(f"🚛 Fleet endpoint accessed with status filter: {status}")
    
    try:
        trucks = db.get_all_trucks()
        
        if status:
            trucks = [t for t in trucks if t.get('status') == status]
        
        # Remove sensitive information
        for truck in trucks:
            truck.pop('driver_phone', None)
            truck.pop('emergency_contact', None)
        
        return {
            "count": len(trucks),
            "status_filter": status,
            "trucks": trucks
        }
    except Exception as e:
        logger.error(f"Error getting fleet: {str(e)}")
        return {"error": "Could not fetch fleet data"}

@app.get("/trips")
async def get_trips(status: str = None, limit: int = 50):
    """Get trip information"""
    logger.info(f"📍 Trips endpoint accessed with status filter: {status}")
    
    try:
        # Use get_all_trips if available, otherwise use _load_json
        if hasattr(db, 'get_all_trips'):
            trips = db.get_all_trips()
        else:
            trips = db._load_json(db.trips_file)
        
        if status:
            trips = [t for t in trips if t.get('status') == status]
        
        # Sort by creation date (newest first)
        trips.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Limit results
        trips = trips[:limit]
        
        return {
            "count": len(trips),
            "status_filter": status,
            "limit": limit,
            "trips": trips
        }
    except Exception as e:
        logger.error(f"Error getting trips: {str(e)}")
        return {"error": "Could not fetch trips data"}

@app.get("/api")
async def api_documentation():
    """API documentation page"""
    return {
        "message": "AI Logistics Agent API",
        "version": "2.0",
        "endpoints": {
            "/": "Main UI and documentation",
            "/message": "POST - Send message to agent",
            "/health": "GET - Health check",
            "/logs": "GET - View application logs",
            "/metrics": "GET - System metrics",
            "/fleet": "GET - Fleet information",
            "/trips": "GET - Trip information",
            "/docs": "GET - Swagger UI documentation",
            "/redoc": "GET - ReDoc documentation"
        },
        "usage": {
            "send_message": "POST /message with form data: message=START TRIP FROM Mumbai TO Delhi&phone=+919999999999",
            "check_health": "GET /health",
            "view_logs": "GET /logs?limit=50&level=ERROR"
        }
    }

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    logger.warning(f"404 Not Found: {request.url}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested URL {request.url} was not found",
            "available_endpoints": [
                "/", "/message", "/health", "/logs", "/metrics", 
                "/fleet", "/trips", "/docs", "/redoc", "/api"
            ]
        }
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"500 Server Error for {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": "N/A"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting AI Logistics Agent server...")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None,
        access_log=False,
        reload=True
    )