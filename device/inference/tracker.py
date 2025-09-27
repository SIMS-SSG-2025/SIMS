from tensorflow.python.framework.test_ops import Simple
from ultralytics.trackers import BYTETracker
from types import SimpleNamespace

class Tracker:
    def __init__(self, class_names, cam_fps):
        args = SimpleNamespace(
            track_buffer=90,
            track_high_thresh=0.5,
            track_low_thresh=0.1,
            new_track_thresh=0.4,
            match_thresh=0.5,
            fuse_score=True
        )
        self.tracker = BYTETracker(args, frame_rate=int(cam_fps))
        self.class_names = class_names

    def update(self, detections, frame):
        height, width, _ = frame.shape
        tracks = self.tracker.update(detections)
        tracked_objects = []
        for track in tracks:
            x1, y1, x2, y2, track_id, conf, cls_id, _ = track
            class_name = self.class_names[int(cls_id)]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)
            tracked_objects.append({
                "track_id": int(track_id),
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "class": class_name,
                "conf": float(conf)
            })

        return tracked_objects
