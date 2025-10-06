import datetime
from database_manager import DatabaseManager


db = DatabaseManager("events.db")
"""
db.insert_object(3,"Oskar")
db.insert_object(4,"Malcolm")

db.insert_zone(6, "[(0,0),(0,10),(10,10),(10,0)]", "Entrance")
db.insert_zone(7, "[(20,20),(20,30),(30,30),(30,20)]", "Warehouse")

db.insert_events(
    object_id=3,
    zone_id=6,
    location="Entrance gate",
    has_helmet=True,
    has_vest=False,
    time=str(datetime.datetime.now())
)

db.insert_events(
    object_id=4,
    zone_id=7,
    location="Back door",
    has_helmet=True,
    has_vest=True,
    time=str(datetime.datetime.now())
)

"""


eventlist = db.get_event()

for event in eventlist:
    event_id,object_id,zone_id,time,has_helmet,has_vest,location = event

    print(f"Event {event_id}:"
          f"Object={object_id}:, Zone={zone_id},Time={time},"
          f"Helmet={bool(has_helmet)}, Vest={bool(has_vest)}",
          f"Location={location}")