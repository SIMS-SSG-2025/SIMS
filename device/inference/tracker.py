"""
Object tracking implementation using BOTSORT algorithm.
Tracks detected objects across video frames, maintaining unique track IDs for
each object. Provides detection result formatting and Re-ID engine integration
for robust multi-object tracking.
"""

from types import SimpleNamespace
from ultralytics.trackers.bot_sort import BOTSORT
import numpy as np
from ultralytics.trackers.basetrack import BaseTrack
from ultralytics import YOLO
from ultralytics.utils.ops import xywh2xyxy
from ultralytics.utils.plotting import save_one_box
import torch
import cv2

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

class ReIDEngine:
    def __init__(self, model_path):
        self.model = YOLO(model_path, task="classify")
        self.model(embed=[-1], imgsz=224)

    def __call__(self, img, dets):
        boxes = xywh2xyxy(torch.from_numpy(dets[:, :4]))

        crops = []
        for box in boxes:
            crop = save_one_box(box, img, save=False)
            crop = cv2.resize(crop, (224, 224))
            crops.append(crop)

        batch_size = 8
        feats = []

        for i in range(0,len(crops),batch_size):
            batch = crops[i:i+batch_size]
            preds = self.model.predict(source=batch, verbose=False, imgsz=224)
            for p in preds[0]:
                feat = p.squeeze()
                if torch.is_tensor(feat):
                    feat = feat.cpu().numpy()

                feats.append(np.squeeze(feat))

        return feats

class Tracker:
    def __init__(self, class_names, cam_fps, with_reid=True, reid_model="./device/training/models/yolo11n-cls.pt"):
        args = SimpleNamespace(
            track_buffer=300,
            track_high_thresh=0.7,
            track_low_thresh=0.05,
            new_track_thresh=0.8,
            match_thresh=0.5,
            fuse_score=True,
            gmc_method="none",
            with_reid=with_reid,
            model=reid_model,
            proximity_thresh=0.35,
            appearance_thresh=0.2
        )

        self.tracker = BOTSORT(args, frame_rate=int(cam_fps))
        self.tracker.encoder = ReIDEngine("device/training/models/yolo11n-cls_dynamic.engine")
        self.class_names = class_names

    def update(self, detections, frame):
        height, width, _ = frame.shape
        _ = self.tracker.update(detections, frame)
        current_frame_id = self.tracker.frame_id

        tracked_objects = []

        alive_tracks = self.tracker.tracked_stracks + self.tracker.lost_stracks

        frame_age_threshold = 30

        for track in alive_tracks:
            track_age = current_frame_id - track.start_frame

            if not track.is_activated or track_age < frame_age_threshold:
                continue

            x1, y1, x2, y2 = track.xyxy

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

            x1, y1, x2, y2 = track.xyxy

            class_name = self.class_names[int(track.cls)]

            in_frame_tracks.append({
                "track_id": int(track.track_id),
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "class": class_name,
                "conf": float(track.score)
            })



        return tracked_objects, in_frame_tracks

    def set_track_id(self,track_id):
        BaseTrack._count = track_id
