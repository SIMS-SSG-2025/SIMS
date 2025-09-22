import cv2
from ultralytics import YOLO
import time

from inference.inference import run_inference
from inference.tracker import Tracker


cam = cv2.VideoCapture(0)
model = YOLO("yolo11n.pt")
class_names = model.names
tracker = Tracker(class_names=class_names)
prev_time = time.time()

while True:
    ret, frame = cam.read()
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    detections = run_inference(rgb_frame, model)
    trackable_classes = ["person", "vehicle"]
    ppe_classes = ["helmet", "vest"]
    detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
    ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
    tracked_objects = tracker.update(detections_for_tracking, frame)
    if tracked_objects is None:
        continue
    for obj in tracked_objects:
        # Visualization
        x, y, w, h = obj["bbox"]
        cls_name = obj["class"]
        track_id = obj["track_id"]
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"Track ID: {track_id} Detected: {cls_name} FPS: {fps:.0f}", (x, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    cv2.imshow('Camera feed', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
