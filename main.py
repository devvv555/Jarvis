"""
J.A.R.V.I.S. Cloud Mobile Backend (Render.com)
Serves the standalone mobile app and provides email checking endpoints for your phone.
"""

import os
import sys
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unified_email import fetch_and_categorize_emails
from notification_hub import notification_hub
from intelligence import (
    get_live_weather, 
    get_overhead_flights, 
    game_theory_analyzer,
    translate_speech,
    human_centric_nav,
    analyze_visual_scene,
    analyze_sleep_telemetry
)

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

from notification_hub import notification_hub

class IngestNotificationPayload(BaseModel):
    app: str
    title: str
    text: str
    priority: str = "normal"

@app.get("/api/notifications")
def get_notifications():
    """Get live feed of phone notifications (WhatsApp, Calls, SMS, College Portal)."""
    return {"notifications": notification_hub.get_all()}

@app.post("/api/push-notification")
def push_notification(payload: IngestNotificationPayload):
    """Webhook for Android MacroDroid / Tasker / KDE Connect to push phone notifications."""
    item = notification_hub.add_notification(payload.app, payload.title, payload.text, payload.priority)
    return {"status": "received", "item": item}

@app.get("/healthz")
def health():
    return {"status": "online", "system": "J.A.R.V.I.S."}

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
    # 4. Meta Glass Live Translation
    elif any(k in q for k in ["translate", "translation", "spanish", "french", "german", "hindi", "tamil"]):
        clean_query = q.replace("translate", "").strip()
        ans = translate_speech(clean_query, "es" if "spanish" in q else "fr" if "french" in q else "hi" if "hindi" in q else "es")
    # 5. Meta Glass Landmark Navigation
    elif any(k in q for k in ["navigate", "directions", "where is", "route to", "take me to"]):
        dest = q.replace("navigate to", "").replace("directions to", "").strip()
        ans = human_centric_nav(dest, payload.lat, payload.lon)
    # 6. Meta Glass "See What You See" Vision
    elif any(k in q for k in ["what am i looking at", "look at this", "see this", "what is this", "scan"]):
        ans = analyze_visual_scene(q)
    # 7. Biometric Sleep Tracker & Readiness
    elif any(k in q for k in ["sleep", "how did i sleep", "sleep score", "recovery", "deep sleep", "rem"]):
        ans = analyze_sleep_telemetry()
    # 8. General conversational query
    else:
        # Clean wake words
        clean_text = q.replace("jarvis", "").strip()
        ans = f"Understood, Sir: '{clean_text}'. How may I assist you further with this?"
        
    return {"answer": ans}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
