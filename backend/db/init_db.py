import sqlite3
import datetime
sqlconn = sqlite3.connect("events.db")

cursor = sqlconn.cursor()
timeslot = datetime.datetime.now()

cursor.execute("""CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY AUTOINCREMENT,
object_id INTEGER NOT NULL,zone_id INTEGER NOT NULL,
time TEXT NOT NULL,
has_helmet INTEGER NOT NULL DEFAULT 0 CHECK(has_helmet IN (0,1)),has_vest INTEGER NOT NULL DEFAULT 0 CHECK(has_helmet IN (0,1)),location TEXT NOT NULL,
FOREIGN KEY (zone_id) REFERENCES zones (zone_id))""")

cursor.execute("""CREATE TABLE IF NOT EXISTS zones (zone_id INTEGER PRIMARY KEY, coords TEXT NOT NULL, name TEXT NOT NULL)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS object (object_id INTEGER PRIMARY KEY ,type TEXT NOT NULL)""")

sqlconn.commit()
sqlconn.close()

