import cv2
from ultralytics import YOLO
import time

from device.inference.inference import run_inference
from device.inference.tracker import Tracker
from device.logic.events import EventManager

import multiprocessing
from multiprocessing import Process, Queue, Event
import threading, queue

import yaml
from ultralytics.nn.tasks import DetectionModel
import torch
from .utils.logger import get_logger
from .utils.db_worker import db_worker

from device.training.dataset.dataset_transform import load_class_mapping

if __name__ == "__main__":
    # -- Setup DB Thread --
    db_queue = queue.Queue(maxsize=100)
    stop_event = threading.Event()
    db_thread = threading.Thread(target=db_worker, args=(db_queue, stop_event))
    db_thread.start()

    # -- Load Model --
    model_config = "device/training/models/yolo11_ppe_cfg.yaml"
    model_path = "device/training/models/yolo_ppe.pth"
    with open(model_config, 'r') as file:
        model_config = yaml.safe_load(file)


    num_classes = model_config["nc"]
    model = DetectionModel(cfg=model_config, nc=num_classes)
    model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage))
    #model_checkpoint = torch.load(model_path)
    #model.load(model_checkpoint)
    model.eval()
    class_names = load_class_mapping("device/training/dataset/safety_dataset_filtered.yaml")
    print(class_names)

    tracker = Tracker(class_names=class_names)
    logger = get_logger("Inference")
    event_manager = EventManager(logger=logger, db_queue=db_queue)

    # -- Capture loop --
    cam = cv2.VideoCapture(0)
    prev_time = time.time()

    while True:
        ret, frame = cam.read()
        if not ret:
            continue
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detections = run_inference(rgb_frame, model)
        trackable_classes = ["Person", "vehicle", "Hardhat", "NO-Hardhat"]
        ppe_classes = ["helmet", "vest"]
        detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
        ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
        tracked_objects = tracker.update(detections_for_tracking, frame)
        event_manager.handle_detections(tracked_objects, ppe_detections)

        ## -- Visualization --
        if tracked_objects:
            for obj in tracked_objects:
                    bbox = obj["bbox"]
                    cx, cy, w, h = bbox
                    x1 = int(cx - w / 2)
                    y1 = int(cy - h / 2)
                    x2 = int(cx + w / 2)
                    y2 = int(cy + h / 2)
                    cls_name = obj["class"]
                    track_id = obj["track_id"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Track ID: {track_id} {cls_name}", (x1, y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            current_time = time.time()
            fps = 1 / (current_time - prev_time)
            prev_time = current_time
            cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Camera feed", frame)

            if cv2.waitKey(1) == ord('q'):
                break

    cam.release()
    cv2.destroyAllWindows()
    stop_event.set()
    db_thread.join()


""" def capture_process(queue, stop_event):
    print("Capture process started.")
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
    print("Capture process exited.")

def inference_process(queue, detection_queue, stop_event, model):
    print("Inference process started.")
    while not stop_event.is_set():
        if not queue.empty():
            frame = queue.get()
            detections = run_inference(frame, model)
            detection_queue.put((detections, frame))
    print("Inference process exited.")


def event_process(detection_queue, visualization_queue, stop_event, tracker, class_names):
    print("Event process started.")
    logger = get_logger("Inference")
    event_manager = EventManager(logger=logger)
    while not stop_event.is_set():
        if not detection_queue.empty():
            detections, frame = detection_queue.get()
            print(detections)
            trackable_classes = ["Person", "vehicle", "Hardhat", "NO-Hardhat"]
            ppe_classes = ["helmet", "vest"]
            detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
            ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
            tracked_objects = tracker.update(detections_for_tracking, frame)
            event_manager.handle_detections(tracked_objects, ppe_detections)
            if tracked_objects is None:
                continue
            for obj in tracked_objects:
                # Visualization
                bbox = obj["bbox"]
                cx, cy, w, h = bbox
                x1 = int(cx - w / 2)
                y1 = int(cy - h / 2)
                x2 = int(cx + w / 2)
                y2 = int(cy + h / 2)
                cls_name = obj["class"]
                track_id = obj["track_id"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Track ID: {track_id} Detected: {cls_name}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            if not visualization_queue.full():
                visualization_queue.put(frame)

    print("Event process exited.")

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn') # Windows specific

    model_config = "device/training/models/yolo11_ppe_cfg.yaml"
    model_path = "device/training/models/yolo_ppe.pth"
    with open(model_config, 'r') as file:
        model_config = yaml.safe_load(file)


    num_classes = model_config["nc"]
    model = DetectionModel(cfg=model_config, nc=num_classes)
    model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage))
    #model_checkpoint = torch.load(model_path)
    #model.load(model_checkpoint)
    model.eval()
    class_names = load_class_mapping("device/training/dataset/safety_dataset_filtered.yaml")
    print(class_names)

    tracker = Tracker(class_names=class_names)
    prev_time = time.time()

    queue = Queue(maxsize=5)
    result_queue = Queue(maxsize=20)
    visualization_queue = Queue(maxsize=5)
    stop_event = Event()

    processes = [
        Process(target=capture_process, args=(queue, stop_event)),
        Process(target=inference_process, args=(queue, result_queue, stop_event, model)),
        Process(target=event_process, args=(result_queue, visualization_queue, stop_event, tracker, class_names))
    ]

    try:
        for p in processes:
            p.start()

        prev_time = time.time()
        while not stop_event.is_set():
            if not visualization_queue.empty():
                frame = visualization_queue.get()
                current_time = time.time()
                fps = 1 / (current_time - prev_time)
                prev_time = current_time
                cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow('Camera feed', frame)
                if cv2.waitKey(1) == ord('q'):
                    stop_event.set()
                    break

        for p in processes:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
                p.join()

    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping processes...")
        stop_event.set()
        for p in processes:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
                p.join()
    except Exception as e:
        print(f"An error occurred: {e}")
        stop_event.set()
        for p in processes:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()
                p.join()
    finally:
        cv2.destroyAllWindows()


 """




""" while True:
    ret, frame = cam.read()
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    detections = run_inference(rgb_frame, model)

    ppe_classes = ["helmet", "vest"]
    # Jämför format på detections
    detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
    ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
    tracked_objects = tracker.update(detections_for_tracking, frame)

    if tracked_objects is None:
        continue
    for obj in tracked_objects:
        # Visualization
        bbox = obj["bbox"]
        cx, cy, w, h = bbox
        x1 = int(cx - w / 2)
        y1 = int(cy - h / 2)
        x2 = int(cx + w / 2)
        y2 = int(cy + h / 2)
        cls_name = obj["class"]
        track_id = obj["track_id"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"Track ID: {track_id} Detected: {cls_name} FPS: {fps:.0f}", (x1, y1+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    cv2.imshow('Camera feed', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows() """
