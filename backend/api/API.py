import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
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
    try:
        rows = db_manager.get_all_events()
        return rows
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise

@app.get("/snapshot")
def take_snapshot():
    try:
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        cam.release()

        if not ret:
            logger.error("Failed to capture image from camera")
            return {"error": "Failed to capture image from camera"}

        # Ensure the snapshot directory exists
        os.makedirs(snapshot_path, exist_ok=True)

         # Save with timestamp to avoid conflicts
        filename = "snapshot_temp.png"
        file_path = os.path.join(snapshot_path, filename)
        cv2.imwrite(file_path, frame)
        return FileResponse(file_path, media_type="image/png")
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        return {"error": f"Failed to take snapshot: {str(e)}"}

@app.post("/zones")
def receive_zones(zone_data: dict):
    try:
        points = zone_data.get("points")
        name = zone_data.get("name", "Unnamed Zone")
        location_id = zone_data.get("location_id", 1)  # Default to location_id 1 for backward compatibility
        if not points:
            logger.warning("No points provided in zone data")
            return {"status": "error", "message": "No points provided"}

        db_manager.insert_zone(points, name, location_id)
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
    try:
        # Check if location already exists
        location_id = db_manager.get_location_by_name(config_data.locationName)

        if location_id is None:
            # Create new location and set it as active
            location_id = db_manager.insert_location_and_activate(config_data.locationName)
        else:
            # Location exists - delete old zones and set as active
            db_manager.delete_zones_by_location(location_id)
            db_manager.set_active_location(location_id)

        # Handle snapshot renaming if temp snapshot exists
        filename = "snapshot_temp.png"
        file_path = os.path.join(snapshot_path, filename)
        if os.path.exists(file_path):
            new_filename = f"snapshot_location_{location_id}.png"
            new_file_path = os.path.join(snapshot_path, new_filename)
            # Remove old snapshot if it exists
            if os.path.exists(new_file_path):
                os.remove(new_file_path)
            os.rename(file_path, new_file_path)
        else:
            logger.warning(f"No snapshot found at {file_path} to rename.")

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
        logger.error(f"Failed to setup configuration: {e}")
        return {
            "status": "error",
            "message": f"Failed to setup configuration: {str(e)}"
        }




@app.get("/logs")
def get_logs():
    try:
        log_path = Path(__file__).resolve().parent.parent.parent / "device" / "logs" / "device.log"
        if log_path.exists():
            with open(log_path, "r") as f:
                lines = f.read().splitlines()
                return {"logs": lines}
        else:
            logger.warning(f"Log file not found at: {log_path}")
            return {"logs": []}
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {e}")
        return {"logs": [], "error": str(e)}




@app.get("/zones/fetch_all")
def get_zones():
    try:
        zones = db_manager.fetch_all_zones()
        return zones
    except Exception as e:
        logger.error(f"Failed to fetch zones: {e}")
        raise

@app.post("/system/start")
def start_system():
    try:
        db_manager.set_ai_running(True)
        return {"status": "AI starting"}
    except Exception as e:
        logger.error(f"Failed to start AI system: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/system/stop")
def stop_system():
    try:
        db_manager.set_ai_running(False)
        return {"status": "AI stopping"}
    except Exception as e:
        logger.error(f"Failed to stop AI system: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/system/status")
def get_status():
    try:
        status = db_manager.get_ai_running()
        return {"status": status}
    except Exception as e:
        logger.error(f"Failed to get AI system status: {e}")
        return {"status": False, "error": str(e)}

@app.get("/config/current")
def get_current_config():
    """
    Get the currently active configuration.
    """
    try:
        location = db_manager.get_active_location()
        if not location:
            return {
                "status": "no_config",
                "message": "No active configuration found"
            }
        location_id, location_name = location
        zones = db_manager.get_zones_by_location(location_id)
        return {
            "status": "success",
            "config": {
                "locationId": location_id,
                "locationName": location_name,
                "zones": zones,
                "snapshotPath": f"/snapshot/{location_id}"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get current configuration: {e}")
        return {
            "status": "error",
            "message": f"Failed to get current configuration: {str(e)}"
        }

@app.delete("/config/current")
def delete_current_config():
    """
    Delete the current (latest) configuration (location and zones).
    """
    try:
        # Get the latest location
        location = db_manager.get_latest_location()
        if not location:
            return {
                "status": "no_config",
                "message": "No configuration to delete"
            }

        location_id = location[0]

        # Delete location and its zones using database manager
        db_manager.delete_location(location_id)

        # Optionally delete the snapshot file
        snapshot_file = os.path.join(snapshot_path, f"snapshot_location_{location_id}.png")
        if os.path.exists(snapshot_file):
            os.remove(snapshot_file)
            logger.info(f"Deleted snapshot for location {location_id}")

        return {
            "status": "success",
            "message": "Configuration deleted successfully"
        }
    except Exception as e:
        logger.error(f"Failed to delete config: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/config/locations")
def get_all_locations():
    """
    Get all locations with their zone counts.
    """
    try:
        rows = db_manager.get_all_locations()

        locations = []
        for row in rows:
            locations.append({
                "locationId": row[0],
                "locationName": row[1],
                "zoneCount": row[2]
            })

        return {
            "status": "success",
            "locations": locations
        }
    except Exception as e:
        logger.error(f"Failed to fetch locations: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/config/location/{location_id}")
def get_config_by_location(location_id: int):
    """
    Get configuration for a specific location.
    """
    try:
        # Get location info using database manager
        location = db_manager.get_location_by_id(location_id)

        if not location:
            return {
                "status": "error",
                "message": "Location not found"
            }

        loc_id, location_name = location

        # Get zones for this location
        zones = db_manager.get_zones_by_location(loc_id)

        return {
            "status": "success",
            "config": {
                "locationId": loc_id,
                "locationName": location_name,
                "zones": zones,
                "snapshotPath": f"/snapshot/{loc_id}"
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch config for location {location_id}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/config/activate/{location_id}")
def activate_location(location_id: int):
    """
    Set a specific location as the active one.
    This will be used for monitoring.
    """
    try:
        location = db_manager.get_location_by_id(location_id)
        if not location:
            return {
                "status": "error",
                "message": "Location not found"
            }

        db_manager.set_active_location(location_id)

        return {
            "status": "success",
            "message": f"Location '{location[1]}' is now active"
        }
    except Exception as e:
        logger.error(f"Failed to activate location: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.delete("/config/location/{location_id}")
def delete_location_config(location_id: int):
    """
    Delete a specific location and its zones.
    """
    try:
        # Delete location and its zones using database manager
        db_manager.delete_location(location_id)

        # Optionally delete the snapshot file
        snapshot_file = os.path.join(snapshot_path, f"snapshot_location_{location_id}.png")
        if os.path.exists(snapshot_file):
            os.remove(snapshot_file)
            logger.info(f"Deleted snapshot for location {location_id}")

        return {
            "status": "success",
            "message": "Location deleted successfully"
        }
    except Exception as e:
        logger.error(f"Failed to delete location {location_id}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/snapshot/{location_id}")
def get_snapshot_by_location(location_id: int):
    try:
        file_path = os.path.join(snapshot_path, f"snapshot_location_{location_id}.png")
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="image/png")
        else:
            logger.warning(f"Snapshot not found for location {location_id}")
            return {"error": "Snapshot not found"}
    except Exception as e:
        logger.error(f"Error retrieving snapshot: {e}")
        return {"error": f"Failed to retrieve snapshot: {str(e)}"}
