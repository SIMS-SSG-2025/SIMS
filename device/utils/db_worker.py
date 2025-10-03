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

    print("DB thread exited.")
