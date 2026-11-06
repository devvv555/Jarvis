"""
J.A.R.V.I.S. Cloud Mobile Backend (Render.com)
Serves the standalone mobile app and provides email checking endpoints for your phone.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unified_email import fetch_and_categorize_emails

app = FastAPI(title="J.A.R.V.I.S. Mobile Cloud")

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/manifest.json")
def manifest():
    manifest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return JSONResponse(content=eval(f.read()))

@app.get("/api/emails")
def get_emails():
    """Endpoint called by your phone to fetch unread personal and college emails."""
    emails = fetch_and_categorize_emails(limit=8)
    return {"emails": emails}

@app.get("/healthz")
def health():
    return {"status": "online", "system": "J.A.R.V.I.S."}

from pydantic import BaseModel
from intelligence import get_live_weather, get_overhead_flights, game_theory_analyzer

class QueryPayload(BaseModel):
    query: str
    lat: float = 11.0168
    lon: float = 76.9558

@app.post("/api/ask")
def ask_jarvis(payload: QueryPayload):
    q = payload.query.lower()
    
    # 1. Flight overhead detection
    if any(k in q for k in ["flight", "plane", "aircraft", "flying above", "overhead", "sky"]):
        ans = get_overhead_flights(payload.lat, payload.lon)
    # 2. Live Weather query
    elif any(k in q for k in ["weather", "temperature", "rain", "forecast", "climate"]):
        ans = get_live_weather(payload.lat, payload.lon)
    # 3. Game Theory & Strategic decision
    elif any(k in q for k in ["game theory", "strategy", "decision", "negotiate", "optimal", "payoff", "nash"]):
        ans = game_theory_analyzer(payload.query)
    # 4. General intelligence fallback
    else:
        ans = (
            f"Analyzing query: '{payload.query}'. At your service, sir. "
            f"All meteorological, airspace, and tactical game theory channels are active."
        )
        
    return {"answer": ans}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
