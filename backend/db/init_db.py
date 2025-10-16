import sqlite3
import datetime
import os

db_path = os.path.join(os.path.dirname(__file__), "events.db")
sqlconn = sqlite3.connect(db_path)

cursor = sqlconn.cursor()
timeslot = datetime.datetime.now()

cursor.execute("""CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY AUTOINCREMENT,
object_id INTEGER NOT NULL,zone_id INTEGER,location_id INTEGER NOT NULL,
time TEXT NOT NULL,
has_helmet INTEGER NOT NULL DEFAULT 0 CHECK(has_helmet IN (0,1)),has_vest INTEGER NOT NULL DEFAULT 0 CHECK(has_vest IN (0,1)),
FOREIGN KEY (zone_id) REFERENCES zones (zone_id),FOREIGN KEY (location_id) REFERENCES location (location_id))""")

cursor.execute("""CREATE TABLE IF NOT EXISTS zones (zone_id INTEGER PRIMARY KEY AUTOINCREMENT,location_id INTEGER NOT NULL,coords TEXT NOT NULL,name TEXT NOT NULL,
FOREIGN KEY (location_id) REFERENCES location (location_id))""")
cursor.execute("""CREATE TABLE IF NOT EXISTS object (object_id INTEGER PRIMARY KEY ,type TEXT NOT NULL)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS location (location_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0,1)))""")
cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (system_config_id INTEGER PRIMARY KEY AUTOINCREMENT, ai_running INTEGER NOT NULL DEFAULT 0 CHECK(ai_running IN (0,1)))""")
cursor.execute("CREATE TABLE IF NOT EXISTS object_positions (id INTEGER PRIMARY KEY AUTOINCREMENT, object_id INTEGER NOT NULL, location TEXT, x REAL NOT NULL, y REAL NOT NULL, time REAL NOT NULL);")
cursor.execute("""INSERT INTO system_config (ai_running) VALUES (1);""")
sqlconn.commit()
sqlconn.close()
