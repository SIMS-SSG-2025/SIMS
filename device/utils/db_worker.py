import sqlite3
import queue
from backend.db.database_manager import DatabaseManager

def db_worker(db_queue, stop_event, db_path="backend/db/events.db"):
    db_manager = DatabaseManager(db_path)


    print("DB thread started.")
    while not stop_event.is_set() or not db_queue.empty():
        try:
            msg = db_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if msg["action"] == "insert_object":
            db_manager.insert_object(msg["object_id"], msg["type"])

        elif msg["action"] == "insert_event":
            db_manager.insert_events(
                msg["object_id"],
                msg["zone_id"],
                msg["location"],
                int(msg["helmet"]),
                int(msg["vest"]),
                msg["time"]
            )

        elif msg["action"] == "get_status":
            status = db_manager.get_ai_running()
            if "response" in msg:
                msg["response"].put(status)

        elif msg["action"] == "set_status":
            db_manager.set_ai_running(msg["status"])
        elif msg["action"] == "get_zones":
            zones = db_manager.fetch_all_zones()
            if "response" in msg:
                msg["response"].put(zones)

        elif msg["action"] == "insert_object_positions":
            data = msg["data"]
            data_db = [
                (d["object_id"], d["location"], d["x"], d["y"], d["time"])
                for d in data
            ]
            db_manager.insert_object_positions(data_db)



    print("DB thread exited.")
