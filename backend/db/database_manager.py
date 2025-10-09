import sqlite3
import json


class DatabaseManager:
    def __init__(self,db_path):
        self.db_path = db_path

    def insert_object(self,object_id,object_type):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO object (object_id,type) VALUES (?,?)""", (object_id,object_type))
        sqlconn.commit()
        sqlconn.close()


    def insert_events(self,object_id,zone_id,location_id,has_helmet,has_vest,time):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO events (object_id,zone_id,location_id,has_helmet,has_vest,time)
        VALUES (?,?,?,?,?,?)""",
        (object_id,zone_id,location_id,has_helmet,has_vest,time))
        sqlconn.commit()
        sqlconn.close()


    def get_event(self):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT * from events")
        rows = cursor.fetchall()
        sqlconn.close()
        return rows

    def insert_zone(self, points,name,location_id):
        coords_json = json.dumps(points)
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO zones (coords,name,location_id) VALUES (?,?,?)""", (coords_json,name))
        sqlconn.commit()
        sqlconn.close()

    def fetch_all_zones(self):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT * from zones")
        rows = cursor.fetchall()
        sqlconn.close()

        zones = []
        for row in rows:
            zone_id,location_id,coords_json,name = row
            coords = json.loads(coords_json)
            zones.append({"zone_id":zone_id,"location_id":location_id,"coords":coords,"name":name})
        return zones

    def set_ai_running(self,value: bool):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("UPDATE system_config SET ai_running=? WHERE system_config_id=1",(1 if value else 0,))
        sqlconn.commit()
        sqlconn.close()

    def get_ai_running(self) -> bool:
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT ai_running FROM system_config WHERE system_config_id=1")
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0] == 1
        return False

    def get_latest_object_id(self):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT MAX(object_id) FROM object")
        result = cursor.fetchone()
        sqlconn.close()
        if result and result[0]:
            return result[0]
        return 0
