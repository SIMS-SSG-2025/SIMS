import os
from fastapi import FastAPI
import sqlite3
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
import cv2
from starlette.responses import StreamingResponse

from ..db.database_manager import DatabaseManager
from pathlib import Path
import json
import time
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