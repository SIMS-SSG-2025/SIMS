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
from device.utils.logger import get_logger

# Initialize logger for API
logger = get_logger("API")

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

logger.info("Initializing FastAPI application")
logger.info(f"Snapshot path: {snapshot_path}")
logger.info(f"Database path: {db_path}")

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
    logger.info("Fetching all events from database")
    try:
        sqlconn = sqlite3.connect(db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT * FROM events")
        rows = cursor.fetchall()
        sqlconn.close()
        logger.info(f"Retrieved {len(rows)} events")
        return rows
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise

@app.get("/snapshot")
def take_snapshot():
    logger.info("Taking camera snapshot")
    try:
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        cam.release()

        if not ret:
            logger.error("Failed to capture image from camera")
            return {"error": "Failed to capture image from camera"}

        # Ensure the snapshot directory exists
        os.makedirs(snapshot_path, exist_ok=True)

        filename = "snapshot.png"
        file_path = os.path.join(snapshot_path, filename)
        cv2.imwrite(file_path, frame)
        logger.info(f"Snapshot saved successfully to {file_path}")
        return FileResponse(file_path, media_type="image/png")
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        return {"error": f"Failed to take snapshot: {str(e)}"}

@app.post("/zones")
def receive_zones(zone_data: dict):
    logger.info(f"Receiving zone data: {zone_data.get('name', 'Unnamed Zone')}")
    try:
        points = zone_data.get("points")
        name = zone_data.get("name", "Unnamed Zone")
        location_id = zone_data.get("location_id", 1)  # Default to location_id 1 for backward compatibility
        if not points:
            logger.warning("No points provided in zone data")
            return {"status": "error", "message": "No points provided"}

        db_manager.insert_zone(points, name, location_id)
        logger.info(f"Zone '{name}' created successfully")
        return {"status": "success", "message": "Zone data received"}
    except Exception as e:
        logger.error(f"Failed to create zone: {e}")
        return {"status": "error", "message": f"Failed to create zone: {str(e)}"}

@app.post("/setup_config")
def setup_config(config_data: ConfigData):
    """
    Setup configuration with location and zones.
    First creates/gets the location, then creates zones with the location_id.
    """
    logger.info(f"Setting up configuration for location: {config_data.locationName}")
    try:
        # Check if location already exists
        location_id = db_manager.get_location_by_name(config_data.locationName)

        if location_id is None:
            # Create new location
            location_id = db_manager.insert_location(config_data.locationName)
            logger.info(f"Created new location: {config_data.locationName} with ID: {location_id}")
        else:
            logger.info(f"Using existing location: {config_data.locationName} with ID: {location_id}")

        # Insert zones for this location
        zone_count = 0
        for zone in config_data.zones:
            db_manager.insert_zone(zone.points, zone.name, location_id)
            zone_count += 1

        logger.info(f"Configuration setup complete: {zone_count} zones created for location {config_data.locationName}")
        return {
            "status": "success",
            "message": f"Configuration setup complete. Location: {config_data.locationName}, Zones: {zone_count}",
            "location_id": location_id,
            "zones_created": zone_count
        }

    except Exception as e:
        logger.error(f"Failed to setup configuration: {e}")
        return {
            "status": "error",
            "message": f"Failed to setup configuration: {str(e)}"
        }




@app.get("/logs")
def get_logs():
    logger.info("Retrieving device logs")
    try:
        log_path = Path(__file__).resolve().parent.parent.parent / "device" / "logs" / "device.log"
        if log_path.exists():
            with open(log_path, "r") as f:
                lines = f.read().splitlines()
                logger.info(f"Retrieved {len(lines)} log lines")
                return {"logs": lines}
        else:
            logger.warning(f"Log file not found at: {log_path}")
            return {"logs": []}
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {e}")
        return {"logs": [], "error": str(e)}


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
    logger.info("Fetching all zones")
    try:
        zones = db_manager.fetch_all_zones()
        logger.info(f"Retrieved {len(zones)} zones")
        return zones
    except Exception as e:
        logger.error(f"Failed to fetch zones: {e}")
        raise

@app.get("/system/start")
def start_system():
    logger.info("Starting AI system")
    try:
        db_manager.set_ai_running(True)
        logger.info("AI system started successfully")
        return {"status": "Ai starting"}
    except Exception as e:
        logger.error(f"Failed to start AI system: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/system/stop")
def stop_system():
    logger.info("Stopping AI system")
    try:
        db_manager.set_ai_running(False)
        logger.info("AI system stopped successfully")
        return {"status": "Ai stopping"}
    except Exception as e:
        logger.error(f"Failed to stop AI system: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/system/status")
def get_status():
    logger.debug("Checking AI system status")
    try:
        status = db_manager.get_ai_running()
        logger.debug(f"AI system status: {status}")
        return {"status": status}
    except Exception as e:
        logger.error(f"Failed to get AI system status: {e}")
        return {"status": False, "error": str(e)}
