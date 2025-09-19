import sqlite3
import datetime
sqlconn = sqlite3.connect("events.db")

cursor = sqlconn.cursor()
timeslot = datetime.datetime.now()

cursor.execute("""CREATE TABLE IF NOT EXISTS events ( id INTEGER PRIMARY KEY AUTOINCREMENT,
               type TEXT NOT NULL,
time TEXT NOT NULL,
has_helmet BOOLEAN,
has_vest BOOLEAN, zone TEXT)""")


sqlconn.commit()
sqlconn.close()

