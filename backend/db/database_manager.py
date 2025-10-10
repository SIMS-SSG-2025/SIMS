import sqlite3
import json


class DatabaseManager:
    def __init__(self,db_path):
        self.db_path = db_path
        self.sqlconn = sqlite3.connect(self.db_path,check_same_thread=False)
        self.cursor = self.sqlconn.cursor()


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
