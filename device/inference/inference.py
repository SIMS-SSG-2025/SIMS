import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import time


# Detection model
model = YOLO("yolo11n.pt")
class_names = model.names

# DeepSort tracker
tracker = DeepSort(max_age=500, n_init=20, max_cosine_distance=0.1, max_iou_distance=0.9)

cam = cv2.VideoCapture(0)

prev_time = time.time()

while True:
    ret, frame = cam.read()
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time


    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = model.predict(rgb_frame, conf=0.8, verbose=False)

    detections = []

    # Extract detections
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()

        for box, score, cls in zip(boxes, scores, class_ids):
            x1, y1, x2, y2 = box
            detections.append(([x1, y1, x2-x1, y2-y1], score, cls,))


    # Tracking
    tracked_detections = tracker.update_tracks(detections, frame=frame)
    for track in tracked_detections:
        if not track.is_confirmed():
            continue

        bbox = track.to_tlwh()
        x, y, w, h = map(int, bbox)
        cls_id = track.get_det_class()
        track_id = track.track_id

        # Visualization
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"Track ID: {track_id} Detected: {class_names[cls_id]} FPS: {fps:.0f}", (x, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)


    cv2.imshow('Camera feed', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
