import sqlite3
import queue

def db_worker(db_queue, stop_event, db_path="backend/db/events.db"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # Ensure tables exist (or move this to migrations)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS object (
        id INTEGER PRIMARY KEY,
        type TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        object_id INTEGER,
        zone_id INTEGER,
        location TEXT,
        helmet BOOLEAN,
        vest BOOLEAN,
        time TEXT
    )
    """)
    conn.commit()

    print("DB thread started.")
    while not stop_event.is_set() or not db_queue.empty():
        try:
            msg = db_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if msg["action"] == "insert_object":
            cursor.execute("INSERT INTO object (id, type) VALUES (?, ?)",
                           (msg["object_id"], msg["object_type"]))
            conn.commit()

        elif msg["action"] == "insert_event":
            cursor.execute("""
            INSERT INTO events (object_id, zone_id, location, helmet, vest, time)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                msg["object_id"], msg["zone_id"], msg["location"],
                msg["helmet"], msg["vest"], msg["time"]
            ))
            conn.commit()

    conn.close()
    print("DB thread exited.")
