import sqlite3


class EventManager:
    def __init__(self,db_path):
        self.db_path = db_path


    def add_event(self,type,event_data):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("""INSERT INTO events (type,time,has_helmet,has_vest,zone)
                          VALUES (?,?,?,?,?)""",
                       (event_data['type'],event_data['time'],
                        int(event_data['has_helmet']),int(event_data['has_vest']),event_data['zone']))
        sqlconn.commit()
        event_id = cursor.lastrowid
        sqlconn.close()
        return event_id

    def get_event(self):
        sqlconn = sqlite3.connect(self.db_path)
        cursor = sqlconn.cursor()
        cursor.execute("SELECT * from events")
        rows = cursor.fetchall()
        sqlconn.close()
        return rows