# app.py

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from pathlib import Path
from whatsapp.webhook import handle_message

app = FastAPI()

# Session storage for phone numbers (in production, use Redis or database)
user_sessions = {}

@app.post("/message")
def message(message: str = Form(...), phone: str = Form("+919999999999")):
    """Handle incoming messages"""
    reply = handle_message(message, phone)
    return {"reply": reply}

@app.get("/")
def ui():
    """Serve the chat interface"""
    html_path = Path("ui/index.html")
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    return HTMLResponse("<h1>UI not found</h1>")

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Logistics Agent v2.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
