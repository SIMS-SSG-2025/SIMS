import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.sqlconn = sqlite3.connect(self.db_path, check_same_thread=False)

    def insert_object(self, object_id, object_type):
        with self.sqlconn:
            self.sqlconn.execute(
                "INSERT INTO object (object_id, type) VALUES (?, ?)",
                (object_id, object_type),
            )

    def insert_events(self, object_id, zone_id, location_id, has_helmet, has_vest, time):
        with self.sqlconn:
            self.sqlconn.execute(
                """INSERT INTO events (object_id, zone_id, location_id, has_helmet, has_vest, time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (object_id, zone_id, location_id, has_helmet, has_vest, time),
            )

    def insert_zone(self, points, name, location_id):
        coords_json = json.dumps(points)
        with self.sqlconn:
            self.sqlconn.execute(
                "INSERT INTO zones (coords, name, location_id) VALUES (?, ?, ?)",
                (coords_json, name, location_id),
            )

    def insert_location(self, name):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "INSERT INTO location (name) VALUES (?)", (name,)
            )
            return cursor.lastrowid

    def insert_location_and_activate(self, name):
        with self.sqlconn:
            self.sqlconn.execute("UPDATE location SET is_active = 0")
            cursor = self.sqlconn.execute(
                "INSERT INTO location (name, is_active) VALUES (?, 1)", (name,)
            )
            return cursor.lastrowid

    def insert_object_positions(self, data):
        if not data:
            return
        with self.sqlconn:
            self.sqlconn.executemany(
                """INSERT INTO object_positions (object_id, location, x, y, time)
                   VALUES (?, ?, ?, ?, ?)""",
                data,
            )


    def set_ai_running(self, value: bool):
        with self.sqlconn:
            self.sqlconn.execute(
                "UPDATE system_config SET ai_running=? WHERE system_config_id=1",
                (1 if value else 0,),
            )

    def set_active_location(self, location_id):
        with self.sqlconn:
            self.sqlconn.execute("UPDATE location SET is_active = 0")
            self.sqlconn.execute(
                "UPDATE location SET is_active = 1 WHERE location_id = ?",
                (location_id,),
            )

    def delete_zones_by_location(self, location_id):
        with self.sqlconn:
            self.sqlconn.execute("DELETE FROM zones WHERE location_id = ?", (location_id,))

    def delete_location(self, location_id):
        with self.sqlconn:
            self.sqlconn.execute("DELETE FROM zones WHERE location_id = ?", (location_id,))
            self.sqlconn.execute(
                "DELETE FROM location WHERE location_id = ?", (location_id,)
            )


    def get_event(self):
        with self.sqlconn:
            cursor = self.sqlconn.execute("SELECT * FROM events")
            return cursor.fetchall()

    def fetch_all_zones(self, location_id):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "SELECT * FROM zones WHERE location_id=?", (location_id,)
            )
            rows = cursor.fetchall()

        zones = []
        for row in rows:
            zone_id, location_id, coords_json, name = row
            coords = json.loads(coords_json)
            zones.append(
                {
                    "zone_id": zone_id,
                    "location_id": location_id,
                    "coords": coords,
                    "name": name,
                }
            )
        return zones

    def get_ai_running(self) -> bool:
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "SELECT ai_running FROM system_config WHERE system_config_id=1"
            )
            result = cursor.fetchone()
            return bool(result and result[0] == 1)

    def get_latest_object_id(self):
        with self.sqlconn:
            cursor = self.sqlconn.execute("SELECT MAX(object_id) FROM object")
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0

    def get_latest_location(self):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "SELECT location_id, name FROM location ORDER BY location_id DESC LIMIT 1"
            )
            return cursor.fetchone()

    def get_active_location(self):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "SELECT location_id, name FROM location WHERE is_active = 1 LIMIT 1"
            )
            return cursor.fetchone()

    def get_zones_by_location(self, location_id):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "SELECT * FROM zones WHERE location_id=?", (location_id,)
            )
            rows = cursor.fetchall()

        zones = []
        for row in rows:
            zone_id, loc_id, coords_json, name = row
            coords = json.loads(coords_json)
            zones.append(
                {"zone_id": zone_id, "location_id": loc_id, "coords": coords, "name": name}
            )
        return zones

    def get_location_by_name(self, name):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "SELECT location_id FROM location WHERE name=?", (name,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_all_locations(self):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                """
                SELECT l.location_id, l.name, COUNT(z.zone_id) as zone_count
                FROM location l
                LEFT JOIN zones z ON l.location_id = z.location_id
                GROUP BY l.location_id, l.name
                ORDER BY l.location_id DESC
                """
            )
            return cursor.fetchall()

    def get_location_by_id(self, location_id):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                "SELECT location_id, name FROM location WHERE location_id = ?",
                (location_id,),
            )
            return cursor.fetchone()

    def get_all_events(self):
        with self.sqlconn:
            cursor = self.sqlconn.execute("SELECT * FROM events")
            return cursor.fetchall()

    def get_events_by_date(self, location_id: int, start_date: str, end_date: str):
        with self.sqlconn:
            cursor = self.sqlconn.execute(
                """
                SELECT * FROM events
                WHERE location_id = ? AND DATE(time) BETWEEN ? AND ?
                ORDER BY time
                """,
                (location_id, start_date, end_date),
            )
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]


    def __del__(self):
        if hasattr(self, "sqlconn"):
            self.sqlconn.close()
