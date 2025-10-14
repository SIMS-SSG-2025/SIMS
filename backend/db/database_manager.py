import sqlite3
import json
from device.utils.logger import get_logger


class DatabaseManager:
    def __init__(self,db_path):
        self.db_path = db_path
        self.sqlconn = sqlite3.connect(self.db_path,check_same_thread=False)
        self.cursor = self.sqlconn.cursor()

        self._configure_pragma()

    def _configure_pragma(self):
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self.cursor.execute("PRAGMA synchronous=NORMAL;")
        self.sqlconn.commit()


    def insert_object(self,object_id,object_type):
        self.cursor.execute("""INSERT INTO object (object_id,type) VALUES (?,?)""", (object_id,object_type))


    def insert_events(self,object_id,zone_id,location_id,has_helmet,has_vest,time):
        self.cursor.execute("""INSERT INTO events (object_id,zone_id,location_id,has_helmet,has_vest,time)
        VALUES (?,?,?,?,?,?)""",
        (object_id,zone_id,location_id,has_helmet,has_vest,time))




    def get_event(self):
        self.cursor.execute("SELECT * from events")
        rows = self.cursor.fetchall()

        return rows

    def insert_zone(self, points,name,location_id):
        coords_json = json.dumps(points)
        self.cursor.execute("""INSERT INTO zones (coords,name,location_id) VALUES (?,?,?)""", (coords_json,name,location_id))

    def fetch_all_zones(self):
        self.cursor.execute("SELECT * from zones")
        rows = self.cursor.fetchall()
        zones = []
        for row in rows:
            zone_id,location_id,coords_json,name = row
            coords = json.loads(coords_json)
            zones.append({"zone_id":zone_id,"location_id":location_id,"coords":coords,"name":name})
        return zones

    def set_ai_running(self,value: bool):
        self.cursor.execute("UPDATE system_config SET ai_running=? WHERE system_config_id=1",(1 if value else 0,))

    def get_ai_running(self) -> bool:
        self.cursor.execute("SELECT ai_running FROM system_config WHERE system_config_id=1")
        result = self.cursor.fetchone()
        if result:
            return result[0] == 1
        return False

    def get_latest_object_id(self):
        self.cursor.execute("SELECT MAX(object_id) FROM object")
        result = self.cursor.fetchone()
        if result and result[0]:
            return result[0]
        return 0

    def get_latest_location(self):
        self.cursor.execute("SELECT location_id, name FROM location ORDER BY location_id DESC LIMIT 1")
        return self.cursor.fetchone()

    def get_zones_by_location(self, location_id):
        self.cursor.execute("SELECT * FROM zones WHERE location_id=?", (location_id,))
        rows = self.cursor.fetchall()
        zones = []
        for row in rows:
            zone_id, loc_id, coords_json, name = row
            coords = json.loads(coords_json)
            zones.append({"zone_id": zone_id, "location_id": loc_id, "coords": coords, "name": name})
        return zones

    def get_location_by_name(self, name):
        self.cursor.execute("SELECT location_id FROM location WHERE name=?", (name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def insert_location(self, name):
        self.cursor.execute("INSERT INTO location (name) VALUES (?)", (name,))
        self.sqlconn.commit()
        return self.cursor.lastrowid

    def insert_object_positions(self, data):
        self.cursor.executemany("""
            INSERT INTO object_positions (object_id, location, x, y, time)
            VALUES (?, ?, ?, ?, ?)
        """, data)
        self.sqlconn.commit()
