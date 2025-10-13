import sqlite3
import json


class DatabaseManager:
    def __init__(self,db_path):
        self.db_path = db_path
        self.sqlconn = sqlite3.connect(self.db_path,check_same_thread=False)
        self.cursor = self.sqlconn.cursor()

    def _location_query(self,specific_location=False):
        query= """SELECT l.name AS location_name,z.name AS zone_name, COUNT(e.event_id) AS total_events,
        SUM(e.has_helmet) AS helmets, SUM(e.has_vest) AS vests FROM events e LEFT JOIN zones z ON e.zone_id = z.zone_id
        LEFT JOIN location l ON e.location_id = l.location_id"""
        if specific_location:
            query += " WHERE e.location_id = ?"
        query += " GROUP BY l.name, z.name"
        return query

    def insert_object(self,object_id,object_type):

        self.cursor.execute("""INSERT INTO object (object_id,type) VALUES (?,?)""", (object_id,object_type))
        self.sqlconn.commit()

    def insert_events(self,object_id,zone_id,location_id,has_helmet,has_vest,time):
        self.cursor.execute("""INSERT INTO events (object_id,zone_id,location_id,has_helmet,has_vest,time)
        VALUES (?,?,?,?,?,?)""",
        (object_id,zone_id,location_id,has_helmet,has_vest,time))
        self.sqlconn.commit()

    def get_event(self):
        self.cursor.execute("SELECT * from events")
        rows = self.cursor.fetchall()

        return rows

    def insert_zone(self, points,name,location_id):
        coords_json = json.dumps(points)
        self.cursor.execute("""INSERT INTO zones (coords,name,location_id) VALUES (?,?,?)""",
        (coords_json,name,location_id))
        self.sqlconn.commit()

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
        self.cursor.execute("UPDATE system_config SET ai_running=? WHERE system_config_id=1",
        (1 if value else 0,))
        self.sqlconn.commit()

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

    def get_events(self):
        self.cursor.execute("SELECT * from events")
        rows = self.cursor.fetchall()
        return rows

    def get_all_location(self):
        query = self._location_query(specific_location=False)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return [{"location": row[0], "zones": row[1],"total_events": row[2],"helmets": row[3],"vests": row[4] or 0}
         for row in rows]


    def get_location(self,location_id):
        query = self._location_query(specific_location=True)
        self.cursor.execute(query,(location_id,))
        rows = self.cursor.fetchall()
        return [{"location": row[0], "zones": row[1], "total_events": row[2], "helmets": row[3], "vests": row[4] or 0}
                for row in rows]