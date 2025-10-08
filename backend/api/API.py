import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import sqlite3
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
import cv2
from ..db.database_manager import DatabaseManager
from pathlib import Path

# Pydantic models for request validation
class ZoneData(BaseModel):
    points: List[dict]
    name: str

class ConfigData(BaseModel):
    locationName: str
    zones: List[ZoneData]

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



@app.get("/events")
def fetch_events():
    sqlconn = sqlite3.connect(db_path)
    cursor = sqlconn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    sqlconn.close()
    return rows

@app.get("/snapshot")
def take_snapshot():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        print("failed to capture")
        return {"error": "Failed to capture image from camera"}

    # Ensure the snapshot directory exists
    os.makedirs(snapshot_path, exist_ok=True)

    filename = "snapshot.png"
    file_path = os.path.join(snapshot_path, filename)
    cv2.imwrite(file_path, frame)
    print(f"Snapshot saved to {file_path}")
    return FileResponse(file_path, media_type="image/png")

@app.post("/zones")
def receive_zones(zone_data: dict):
    points = zone_data.get("points")
    name = zone_data.get("name", "Unnamed Zone")
    location_id = zone_data.get("location_id", 1)  # Default to location_id 1 for backward compatibility
    if not points:
        return {"status": "error", "message": "No points provided"}
    db_manager.insert_zone(points, name, location_id)
    return {"status": "success", "message": "Zone data received"}

@app.post("/setup_config")
def setup_config(config_data: ConfigData):
    """
    Setup configuration with location and zones.
    First creates/gets the location, then creates zones with the location_id.
    """
    try:
        # Check if location already exists
        location_id = db_manager.get_location_by_name(config_data.locationName)

        if location_id is None:
            # Create new location
            location_id = db_manager.insert_location(config_data.locationName)
            print(f"Created new location: {config_data.locationName} with ID: {location_id}")
        else:
            print(f"Using existing location: {config_data.locationName} with ID: {location_id}")

        # Insert zones for this location
        zone_count = 0
        for zone in config_data.zones:
            db_manager.insert_zone(zone.points, zone.name, location_id)
            zone_count += 1

        return {
            "status": "success",
            "message": f"Configuration setup complete. Location: {config_data.locationName}, Zones: {zone_count}",
            "location_id": location_id,
            "zones_created": zone_count
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to setup configuration: {str(e)}"
        }




@app.get("/logs")
def get_logs():
    log_path = Path(__file__).resolve().parent.parent.parent / "device" / "logs" / "device.log"
    if log_path.exists():
        with open(log_path, "r") as f:
            lines = f.read().splitlines()
            return {"logs": lines}
    return {"logs": []}


"""
@app.get("/zones/stream")
def stream_zones():
    def event_stream():
        last_id = set()
        while True:
            zones = DatabaseManager.fetch_zones()
            current_id = set([z['zone_id'] for z in zones])

            if current_id != last_id:
                last_id = current_id
                yield f" data: {json.dumps(zones)}\n\n"
            time.sleep(1)
    return StreamingResponse(event_stream(), media_type="text/event-stream")
"""

@app.get("/zones/fetch_all")
def get_zones():
    zones = db_manager.fetch_all_zones()
    return zones

@app.get("/system/start")
def start_system():
    db_manager.set_ai_running(True)
    return {"status": "Ai starting"}

@app.get("/system/stop")
def stop_system():
    db_manager.set_ai_running(False)
    return {"status": "Ai stopping"}

@app.get("/system/status")
def get_status():
    status = db_manager.get_ai_running()
    return {"status": status}
