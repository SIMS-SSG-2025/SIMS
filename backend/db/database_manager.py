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


    def insert_events(self,object_id,zone_id,location,has_helmet,has_vest,time):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO events (object_id,zone_id,location,has_helmet,has_vest,time)
        VALUES (?,?,?,?,?,?)""",
        (object_id,zone_id,location,has_helmet,has_vest,time))
        sqlconn.commit()
        sqlconn.close()


    def get_event(self):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT * from events")
        rows = cursor.fetchall()
        sqlconn.close()
        return rows

    def insert_zone(self, points, name):
        coords_json = json.dumps(points)
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO zones (coords,name) VALUES (?,?)""", (coords_json,name))
        sqlconn.commit()
        sqlconn.close()
