import os
from backend.db.database_manager import DatabaseManager
import datetime
from shapely.geometry import Point, Polygon

class EventManager:
    def __init__(self, logger, db_queue, class_names):
        self.active_tracks = []
        self.zones = []  # Predefined zones can be added here
        #db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", "db", "events.db")
        self.db_queue = db_queue
        #self.database = DatabaseManager(db_path=db_path)
        self.logger = logger
        self.class_names = class_names

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
                if obj["class"] == "Person":
                    obj["ppe"] = []
                    for ppe in ppe_detections:
                        if self._is_overlapping(obj["bbox"], ppe[0]):
                            obj["ppe"].append(self.class_names[ppe[2]])

                self._create_object(obj)
                self._create_event(obj)

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
        x, y, w, h = bbox
        x_center = (x + w) / 2
        y_feet = y + h
        point = Point(x_center, y_feet)
        for zone in self.zones:
            polygon = Polygon(zone["coords"])
            if polygon.contains(point):
                return True
        return False

    def _create_object(self, obj):
        """ Create an object in the database. """

        object_msg = {
            "action": "insert_object",
            "object_id": obj["track_id"],
            "type": obj["class"],
        }

        self.logger.info(f"[DB] Object created: {object_msg}")
        self.db_queue.put(object_msg)
        print(f"Object created: {object_msg}")


    def _create_event(self, obj):
        """ Create an event in the database. """

        event_msg = {
            "action": "insert_event",
            "object_id": obj["track_id"],
            "zone_id": None,
            "location": "lager1",
            "helmet": True if "Hardhat" in obj.get("ppe", []) else False,
            "vest": True if "Safety Vest" in obj.get("ppe", []) else False,
            "time": datetime.datetime.now().isoformat(),
        }
        self.logger.info(f"[DB] Event created: {event_msg}")
        self.db_queue.put(event_msg)
        print(f"Event created: {event_msg}")

    def set_zones(self, zones):
        self.zones = zones


    def get_zones(self):
        return self.zones

