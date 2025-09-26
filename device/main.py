import cv2
from ultralytics import YOLO
import time

from device.inference.inference import run_inference
from device.inference.tracker import Tracker
from device.logic.events import EventManager

from multiprocessing import Process, Queue, Event

def capture_process(queue, stop_event):
    cam = cv2.VideoCapture(0)
    while not stop_event.is_set():
        ret, frame = cam.read()
        if not ret:
            continue
        if not queue.full():
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            queue.put(rgb_frame)
        time.sleep(0.01)

    cam.release()

def inference_process(queue, detection_queue, stop_event):
    while not stop_event.is_set():
        if not queue.empty():
            frame = queue.get()
            detections = run_inference(frame, model)
            detection_queue.put((detections, frame))



def event_process(detection_queue, stop_event):
    while not stop_event.is_set():
        if not detection_queue.empty():
            detections, frame = detection_queue.get()
            trackable_classes = ["person", "vehicle"]
            ppe_classes = ["helmet", "vest"]
            detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
            ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
            tracked_objects = tracker.update(detections_for_tracking, frame)
            event_manager.handle_detections(tracked_objects, ppe_detections)
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
                stop_event.set()
                break

    cv2.destroyAllWindows()



if __name__ == "__main__":

    model = YOLO("yolo11n.pt")
    class_names = model.names
    tracker = Tracker(class_names=class_names)
    event_manager = EventManager()
    prev_time = time.time()

    queue = Queue(maxsize=5)
    result_queue = Queue(maxsize=20)
    stop_event = Event()

    p1 = Process(target=capture_process, args=(queue, stop_event))
    p2 = Process(target=inference_process, args=(queue, result_queue, stop_event))
    p3 = Process(target=event_process, args=(result_queue, stop_event))
    p1.start()
    p2.start()
    p3.start()

    p1.join()
    p2.join()
    p3.join()



""" while True:
    ret, frame = cam.read()
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    detections = run_inference(rgb_frame, model)
    print(detections)
    trackable_classes = ["person", "vehicle"]
    ppe_classes = ["helmet", "vest"]
    detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
    ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
    tracked_objects = tracker.update(detections_for_tracking, frame)
    #event_manager.handle_detections(tracked_objects, ppe_detections)
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
cv2.destroyAllWindows() """
