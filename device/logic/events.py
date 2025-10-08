import os
from backend.db.database_manager import DatabaseManager
import datetime


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
        Check for new objects
        tracked_objects: [{track_id: 1, bbox: [x1, y1, x2, y2], cls: "Person", conf: 0.9}]
        ppe_detections: [(([x1, y1, x2, y2]), conf, class_id)]
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





    def _is_overlapping(self, bbox1, bbox2, iou_threshold=0.8):
        """
        Computes iou and returns true if bbox1 and bbox2 exceeds iou_threshold.
        bbox: [x1, y1, x2, y2]
        """
        inter_x1 = max(bbox1[0], bbox2[0])
        inter_y1 = max(bbox1[1], bbox2[1])
        inter_x2 = min(bbox1[2], bbox2[2])
        inter_y2 = min(bbox1[3], bbox2[3])

        area1 = max(0, bbox1[2] - bbox1[0]) * max(0, bbox1[3] - bbox1[1])
        area2 = max(0, bbox2[2] - bbox2[0]) * max(0, bbox2[3] - bbox2[1])

        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

        union_area = area1 + area2 - inter_area

        if union_area == 0:
            return False

        return (inter_area / union_area) >= iou_threshold

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


