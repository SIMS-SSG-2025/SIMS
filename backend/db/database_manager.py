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

    def update_zone(self, zone_id, points, name):
        """Update an existing zone's points and name"""
        with self.sqlconn:
            cursor = self.sqlconn.cursor()
            cursor.execute(
                "UPDATE zones SET coords = ?, name = ? WHERE zone_id = ?",
                (str(points), name, zone_id)
            )
            return cursor.rowcount > 0

    def get_zone_by_name_and_location(self, name, location_id):
        """Get a zone by name and location_id"""
        with self.sqlconn:
            cursor = self.sqlconn.cursor()
            cursor.execute(
                "SELECT zone_id, coords, name FROM zones WHERE name = ? AND location_id = ?",
                (name, location_id)
            )
            row = cursor.fetchone()
            if row:
                return {"zone_id": row[0], "coords": row[1], "name": row[2]}
            return None

    def upsert_zones_for_location(self, zones_data, location_id):
        """
        Update existing zones or insert new ones for a location.
        Matches zones by name to preserve zone_ids in events.
        Returns list of zone_ids created/updated.
        """
        zone_ids = []

        # Get existing zones for this location
        existing_zones = {}
        with self.sqlconn:
            cursor = self.sqlconn.cursor()
            cursor.execute(
                "SELECT zone_id, name FROM zones WHERE location_id = ?",
                (location_id,)
            )
            for row in cursor.fetchall():
                existing_zones[row[1]] = row[0]  # name -> zone_id

        # Track which zones we've processed
        processed_zone_names = set()

        # Update existing zones or insert new ones
        for zone_data in zones_data:
            zone_name = zone_data.get("name", "Unnamed Zone")
            points = zone_data.get("points", [])

            if zone_name in existing_zones:
                # Update existing zone
                zone_id = existing_zones[zone_name]
                self.update_zone(zone_id, points, zone_name)
                zone_ids.append(zone_id)
            else:
                # Insert new zone
                zone_id = self.insert_zone(points, zone_name, location_id)
                zone_ids.append(zone_id)

            processed_zone_names.add(zone_name)

        # Delete zones that are no longer in the config
        for zone_name, zone_id in existing_zones.items():
            if zone_name not in processed_zone_names:
                with self.sqlconn:
                    self.sqlconn.execute("DELETE FROM zones WHERE zone_id = ?", (zone_id,))

        return zone_ids

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
