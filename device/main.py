import cv2
import time

import numpy as np


from inference.inference import run_inference
from inference.tracker import Tracker
from logic.events import EventManager
import yaml
from ultralytics.nn.tasks import DetectionModel
import torch
from training.dataset.dataset_transform import load_class_mapping
import onnxruntime as ort

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



cam = cv2.VideoCapture(0)
cam_fps = cam.get(cv2.CAP_PROP_FPS)
print(f"Cam FPS: {cam_fps}")

onnx_model_path = "training/models/yolo_ppe.onnx"
session = ort.InferenceSession(onnx_model_path)


print("Inputs:", [i.name for i in session.get_inputs()])
print("Outputs:", [o.name for o in session.get_outputs()])


#class_names = model.names
class_names = load_class_mapping("training/dataset/safety_dataset_filtered.yaml")
print(class_names)
tracker = Tracker(class_names=class_names, cam_fps=cam_fps)
event_manager = EventManager()
prev_time = time.time()

while True:
    ret, frame = cam.read()
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    detections = run_inference(rgb_frame, session)

    trackable_classes = ["Person", "vehicle", "Hardhat", "NO-Hardhat"]
    ppe_classes = ["helmet", "vest"]
    detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
    results = DetectionResults(detections_for_tracking)
    ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
    tracked_objects = tracker.update(results, frame)
    #event_manager.handle_detections(tracked_objects, ppe_detections)
    if tracked_objects is None:
        continue
    for obj in tracked_objects:
        # Visualization
        bbox = obj["bbox"]
        x1, y1, x2, y2 = bbox
        cls_name = obj["class"]
        track_id = obj["track_id"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"Track ID: {track_id} Detected: {cls_name} FPS: {fps:.0f}", (x1, y1+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    cv2.imshow('Camera feed', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
