import os
from fastapi import FastAPI
import sqlite3
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
import cv2
from ..db.database_manager import DatabaseManager
from pathlib import Path
app = FastAPI()
snapshot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"device", "snapshot")
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db","events.db")
db_manager = DatabaseManager(db_path)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/locations")
def fetch_all_locations():
    return db_manager.get_all_location()

@app.get("/locations/{location_id}")
def fetch_location(location_id: int):
    return db_manager.get_location(location_id)

@app.get("/snapshot")

def take_snapshot():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        print("failed to capture")

    filename = "snapshot.png"
    file_path = os.path.join(snapshot_path, filename)
    cv2.imwrite(file_path, frame)
    return FileResponse(file_path, media_type="image/png")

@app.post("/zones")
def receive_zones(zone_data: dict):
    points = zone_data.get("points")
    name = zone_data.get("name", "Unnamed Zone")
    if not points:
        return {"status": "error", "message": "No points provided"}
    db_manager.insert_zone(points, name)
    return {"status": "success", "message": "Zone data received"}




@app.get("/logs")
def get_logs():
    log_path = Path(__file__).resolve().parent.parent.parent / "device" / "logs" / "device.log"
    if log_path.exists():
        with open(log_path, "r") as f:
            lines = f.read().splitlines()
            return {"logs": lines}
    return {"logs": []}




@app.get("/zones/fetch_all")
def get_zones():
    zones = DatabaseManager.fetch_all_zones()
    return zones

@app.get("/system/start")
def start_system():
    db_manager.set_system_config(True)
    return {"status": "Ai starting"}

@app.get("/system/stop")
def stop_system():
    db_manager.set_system_config(False)
    return {"status": "Ai stopping"}

@app.get("/system/status")
def get_status():
    status = db_manager.get_ai_running()
    return {"status": status}

