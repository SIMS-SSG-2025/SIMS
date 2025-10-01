import sqlite3
import datetime
import os

db_path = os.path.join(os.path.dirname(__file__), "events.db")
sqlconn = sqlite3.connect(db_path)

cursor = sqlconn.cursor()
timeslot = datetime.datetime.now()

cursor.execute("""CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY AUTOINCREMENT,
object_id INTEGER NOT NULL,zone_id INTEGER NOT NULL,
time TEXT NOT NULL,
has_helmet INTEGER NOT NULL DEFAULT 0 CHECK(has_helmet IN (0,1)),has_vest INTEGER NOT NULL DEFAULT 0 CHECK(has_vest IN (0,1)),location TEXT NOT NULL,
FOREIGN KEY (zone_id) REFERENCES zones (zone_id))""")

cursor.execute("""CREATE TABLE IF NOT EXISTS zones (zone_id INTEGER PRIMARY KEY AUTOINCREMENT, coords TEXT NOT NULL, name TEXT NOT NULL)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS object (object_id INTEGER PRIMARY KEY, type TEXT NOT NULL)""")

sqlconn.commit()
sqlconn.close()
