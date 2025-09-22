import sqlite3


class DatabaseManager:
    def __init__(self,db_path):
        self.db_path = db_path


    def insert_object(self,object_id,object_type):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO object (object_id,type) VALUES (?,?)""", (object_id,object_type))
        sqlconn.commit()
        sqlconn.close()


    def insert_zone(self,zone_id,coords,name):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO zones (zone_id,coords,name) VALUES (?,?,?)""", (zone_id,coords,name))
        sqlconn.commit()
        sqlconn.close()




    def insert_events(self,object_id,zone_id,type,location,ppe,time):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO events (object_id,zone_id,type,location,ppe,time)
        VALUES (?,?,?,?,?,?)""",
        (object_id,zone_id,type,location,ppe,time))
        sqlconn.commit()
        sqlconn.close()


    def get_event(self):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT * from events")
        rows = cursor.fetchall()
        sqlconn.close()
        return rows