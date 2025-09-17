import sqlite3
import datetime
sqlconn = sqlite3.connect("events.db")

cursor = sqlconn.cursor()
timeslot = datetime.datetime.now()

cursor.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, type TEXT, time TEXT)")
cursor.execute("INSERT INTO events (type,time) VALUES (?, ?)", ("Filip",  f"{timeslot}"))

cursor.execute("SELECT * from events")

# print(cursor.fetchall())
sqlconn.commit()
sqlconn.close()

