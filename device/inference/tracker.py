from types import SimpleNamespace
from ultralytics.trackers.bot_sort import BOTSORT
from ultralytics.trackers.basetrack import BaseTrack
import numpy as np

class DetectionResults:
    def __init__(self, dets):
        flat_dets = []
        for det in dets:
            bbox, conf, cls = det
            flat_dets.append(list(bbox) + [conf, cls])

        dets_array = np.array(flat_dets, dtype=np.float32)

        if dets_array.size == 0:
            self.xywh = np.zeros((0, 4), dtype=np.float32)
            self.conf = np.zeros((0,), dtype=np.float32)
            self.cls = np.zeros((0,), dtype=int)
        else:
            self.xywh = dets_array[:, :4]
            self.conf = dets_array[:, 4]
            self.cls = dets_array[:, 5].astype(int)

class Tracker:
    def __init__(self, class_names, cam_fps, with_reid=True, reid_model="yolov8n-cls.pt"):
        args = SimpleNamespace(
            track_buffer=360,
            track_high_thresh=0.3,
            track_low_thresh=0.1,
            new_track_thresh=0.3,
            match_thresh=0.4,
            fuse_score=True,
            gmc_method="none",
            with_reid=with_reid,
            model=reid_model,
            proximity_thresh=0.3,
            appearance_thresh=0.25
        )

        self.tracker = BOTSORT(args, frame_rate=int(cam_fps))
        # BaseTrack._count = 12 # Get latest object id from db
        # self.tracker.encoder.model.device.to("cuda") to gpu
        self.class_names = class_names

    def update(self, detections, frame):
        height, width, _ = frame.shape
        _ = self.tracker.update(detections, frame)
        current_frame_id = self.tracker.frame_id

        tracked_objects = []

        alive_tracks = self.tracker.tracked_stracks + self.tracker.lost_stracks

        frame_age_threshold = 5

        for track in alive_tracks:
            track_age = current_frame_id - track.start_frame

            if not track.is_activated or track_age < frame_age_threshold:
                continue

            tlwh = track.tlwh
            x1, y1, w, h= tlwh
            x2 = x1 + w
            y2 = y1 + h

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)

            class_name = self.class_names[int(track.cls)]

            tracked_objects.append({
                "track_id": int(track.track_id),
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "class": class_name,
                "conf": float(track.score)
            })

        in_frame_tracks = []

        for track in self.tracker.tracked_stracks:
            track_age = current_frame_id - track.start_frame

            if not track.is_activated or track_age < frame_age_threshold:
                continue


            tlwh = track.tlwh
            x1, y1, w, h= tlwh
            x2 = x1 + w
            y2 = y1 + h

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)

            class_name = self.class_names[int(track.cls)]

            in_frame_tracks.append({
                "track_id": int(track.track_id),
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "class": class_name,
                "conf": float(track.score)
            })



        return tracked_objects, in_frame_tracks
