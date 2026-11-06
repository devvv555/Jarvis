"""
J.A.R.V.I.S. Control Server & Desktop App
Serves the control interface locally and opens it directly in a dedicated app window.
"""

import os
import sys
import webbrowser
import subprocess
import threading
import time

# Ensure local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import socket
import io
import base64
import qrcode
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from app_manager import AppManager
from notifications import NotificationManager
from diagnostics import Diagnostics

app = FastAPI(title="JARVIS Control Center")
apps_mgr = AppManager()
notifier = NotificationManager("J.A.R.V.I.S.")
diag = Diagnostics()

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.get("/api/phone-connect")
def get_phone_connect_info():
    ip = get_lan_ip()
    phone_url = f"http://{ip}:8088"
    
    # Generate QR Code image in base64
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(phone_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#38bdf8", back_color="#0b0f19")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return {
        "ip": ip,
        "url": phone_url,
        "qr_base64": f"data:image/png;base64,{img_b64}"
    }

class NotifyPayload(BaseModel):
    title: str
    message: str

class LaunchPayload(BaseModel):
    appName: str

class KillPayload(BaseModel):
    target: str

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/vitals")
def get_vitals():
    return diag.get_system_vitals()

@app.get("/api/processes")
def get_processes():
    return apps_mgr.list_running_apps(limit=15)

@app.post("/api/launch")
def launch_app(payload: LaunchPayload):
    success, msg = apps_mgr.launch(payload.appName)
    if success:
        notifier.notify("App Launched", f"Started: {payload.appName}")
    return {"success": success, "message": msg}

@app.post("/api/close")
def close_process(payload: KillPayload):
    success, msg = apps_mgr.close(payload.target)
    return {"success": success, "message": msg}

@app.post("/api/notify")
def send_notification(payload: NotifyPayload):
    notifier.notify(payload.title, payload.message)
    return {"success": True, "message": "Notification dispatched."}

@app.post("/api/preset/{mode}")
def run_preset(mode: str):
    if mode == "study":
        apps_mgr.launch("code")
        apps_mgr.launch("chrome")
        notifier.notify("Study Mode", "Development tools opened. Time to focus!")
        return {"success": True, "message": "Study Mode active."}
    elif mode == "break":
        apps_mgr.launch("spotify")
        notifier.notify("Break Time", "Take a short break and recharge!")
        return {"success": True, "message": "Break Mode active."}
    elif mode == "clean":
        for a in ["notepad", "calc"]:
            apps_mgr.close(a)
        notifier.notify("Cleanup Complete", "Closed background utilities.")
        return {"success": True, "message": "Clutter cleared."}
    return {"success": False, "message": "Unknown mode."}

@app.post("/api/floating-bar")
def launch_floating_bar():
    py_exec = sys.executable
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "floating_bar.py")
    subprocess.Popen([py_exec, script_path])
    return {"success": True, "message": "Floating Command Bar summoned."}

def open_window():
    time.sleep(1.2)
    url = "http://localhost:8088"
    # Try launching in Chrome app mode (clean app window without browser bars)
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    
    launched = False
    for p in chrome_paths:
        if os.path.exists(p):
            subprocess.Popen([p, f"--app={url}", "--window-size=950,700"])
            launched = True
            break
            
    if not launched:
        for p in edge_paths:
            if os.path.exists(p):
                subprocess.Popen([p, f"--app={url}", "--window-size=950,700"])
                launched = True
                break

    if not launched:
        webbrowser.open(url)

if __name__ == "__main__":
    threading.Thread(target=open_window, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8088, log_level="warning")
