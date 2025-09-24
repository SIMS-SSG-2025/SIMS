from backend.db.database_manager import DatabaseManager
import datetime


class EventManager:
    def __init__(self):
        self.active_tracks = []
        self.zones = []  # Predefined zones can be added here
        self.database = DatabaseManager(db_path="events.db")

    def handle_detections(self, tracked_objects, ppe_detections):
        """
        Handles detections.
        Creates or updates events in DB as needed.
        Check for new object
        tracked_objects: {track_id: 1, bbox: [x, y, w, h], cls: "person"}
        ppe_detections: [{"bbox": [x, y, w, h], "class_id": "helmet", "score": 0.9}]
        """
        if tracked_objects is None:
            return
        for obj in tracked_objects:
            track_id = obj["track_id"]

            if track_id not in self.active_tracks:
                # New object detected
                self.active_tracks.append(track_id)
                if obj["class"] == "person":
                    obj["ppe"] = []
                    for ppe in ppe_detections:
                        if self._is_overlapping(obj["bbox"], ppe["bbox"]):
                            obj["ppe"].append(ppe["class"])

                self._create_object(obj)



        self.active_tracks = [obj["track_id"] for obj in tracked_objects]





    def _is_overlapping(self, bbox1, bbox2):
        """
        Check if two bounding boxes overlap.
        bbox: [x, y, w, h]
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2

        if (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2):
            return True
        return False

    def _check_zone(self, bbox):
        """
        Check if the bbox is in a predefined zone.
        For simplicity, let's say zone is defined as x > 100 and y > 100
        """
        x, y, w, h = bbox
        if x > 100 and y > 100:
            return True
        return False
    def _create_object(self, obj):
        """ Create an object in the database. """
        object = {
            "track_id": obj["track_id"],
            "type": obj["class"],
        }
        print(f"Object created: {object}")
        # Here you would insert the object into your database
        self.database.insert_object(object_id=object["track_id"], object_type=object["type"])

    def _create_event(self, obj):
        """ Create an event in the database. """

        event = {
            "object_id": obj["track_id"],
            "zone_id": None,
            "location": "lager1",
            "helmet": True if "helmet" in obj.get("ppe", []) else False,
            "vest": True if "vest" in obj.get("ppe", []) else False,
            "time": datetime.datetime.now().isoformat(),
        }
        print(f"Event created: {event}")
        # Here you would insert the event into your database
        self.database.insert_events(
            object_id=event["object_id"],
            zone_id=event["zone_id"],
            location=event["location"],
            helmet=event["helmet"],
            vest=event["vest"],
            time=event["time"]
        )
