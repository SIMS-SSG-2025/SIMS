import os
from backend.db.database_manager import DatabaseManager
import datetime

from shapely.geometry import Point, Polygon

from ..utils.logger import get_logger


class EventManager:
    def __init__(self, logger, db_queue, class_names):
        self.active_tracks = set()
        self.in_zone_objects = set()
        self.zones = None  # Predefined zones can be added here
        # db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", "db", "events.db")
        self.db_queue = db_queue
        # self.database = DatabaseManager(db_path=db_path)
        self.logger = logger
        self.detection_logger = get_logger("DETECTION")
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
                self.active_tracks.add(track_id)
                if obj["class"] == "Person":
                    obj["ppe"] = []
                    for ppe in ppe_detections:
                        if self._is_overlapping(obj["bbox"], ppe[0]):
                            obj["ppe"].append(self.class_names[ppe[2]])

                self._create_object(obj)
                self._create_event(obj)



            if self.zones and obj["class"] == "Person":
                for zone in self.zones:
                    in_zone = self._check_zone(obj["bbox"], zone["coords"])
                    # If an object has entered the zone - Create an event in the database
                    if in_zone and obj["track_id"] not in self.in_zone_objects:
                        self._create_event(obj, zone["zone_id"])
                        self.in_zone_objects.add(obj["track_id"])
                        break
                    # If an object leaves the zone - Remove track_id from in_zone_objects
                    elif not in_zone and obj["track_id"] in self.in_zone_objects:
                        self.in_zone_objects.remove(obj["track_id"])
                        break


        self.active_tracks = {obj["track_id"] for obj in tracked_objects}
        self.in_zone_objects = {
            idx for idx in self.in_zone_objects if idx in self.active_tracks
        }


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

    def _check_zone(self, bbox, zone):
        x1, y1, x2, y2 = bbox
        x_center = (x1 + x2) / 2
        y_feet = y2
        point = Point(x_center, y_feet)
        polygon = Polygon(zone)
        if polygon.contains(point):
            return True
        return False

    def _create_object(self, obj):
        """ Create an object in the database. """
        try:
            object_msg = {
                "action": "insert_object",
                "object_id": obj["track_id"],
                "type": obj["class"],
            }

            self.logger.info(f"Creating object: ID={obj['track_id']}, Type={obj['class']}")
            self.db_queue.put(object_msg)

        except Exception as e:
            self.logger.error(f"Failed to create object: {e}")

    def _create_event(self, obj, zone_id=None):
        """ Create an event in the database. """
        try:
            has_helmet = "Hardhat" in obj.get("ppe", [])
            has_vest = "Safety Vest" in obj.get("ppe", [])

            event_msg = {
                "action": "insert_event",
                "object_id": obj["track_id"],
                "zone_id": zone_id,
                "location": "lager1",
                "helmet": has_helmet,
                "vest": has_vest,
                "time": datetime.datetime.now().isoformat(),
            }

            safety_status = []
            if has_helmet:
                safety_status.append("helmet")
            if has_vest:
                safety_status.append("vest")

            safety_str = f"with {', '.join(safety_status)}" if safety_status else "without PPE"
            self.logger.info(f"Creating event: Object {obj['track_id']} detected {safety_str}")
            self.detection_logger.info(f"Detected {obj['class']} with ID {obj['track_id']} {safety_str}")

            self.db_queue.put(event_msg)

        except Exception as e:
            self.logger.error(f"Failed to create event: {e}")

    def set_zones(self, zones, frame_width, frame_height):
        processed_zones = []

        for zone in zones:
            pixel_coords = []
            for point in zone["coords"]:
                x = int(point['x'] * frame_width)
                y = int(point['y'] * frame_height)
                pixel_coords.append([x, y])
            processed_zone = {
                'zone_id': zone["zone_id"],
                'location_id': zone["location_id"],
                'coords': pixel_coords,
                'name': zone["name"],
            }

            processed_zones.append(processed_zone)

        self.zones = processed_zones

    def get_zones(self):
        return self.zones

    def get_zones_coords(self):
        zone_coords = []
        for zone in self.zones:
            coords = zone["coords"]
            zone_coords.append(coords)
        return zone_coords
