import cv2
from ultralytics import YOLO
import time

from device.inference.inference import run_inference
from device.inference.tracker import Tracker, DetectionResults
from device.logic.events import EventManager

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

    # -- Capture loop --
    cam = cv2.VideoCapture(0)
    cam_fps = cam.get(cv2.CAP_PROP_FPS)
    print(f"Cam FPS: {cam_fps}")
    prev_time = time.time()

    tracker = Tracker(class_names=class_names, cam_fps=cam_fps)
    logger = get_logger("Inference")
    event_manager = EventManager(logger=logger, db_queue=db_queue)

    while True:
        ret, frame = cam.read()
        if not ret:
            continue
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detections = run_inference(rgb_frame, model)
        trackable_classes = ["Person", "vehicle"]
        ppe_classes = ["helmet", "vest"]
        detections_for_tracking = [d for d in detections if class_names[d[-1]] in trackable_classes]
        results = DetectionResults(detections_for_tracking)
        ppe_detections = [d for d in detections if class_names[d[-1]] in ppe_classes]
        tracked_objects = tracker.update(results, frame)
        # event_manager.handle_detections(tracked_objects, ppe_detections)

        ## -- Visualization --
        if tracked_objects:
            for obj in tracked_objects:
                    bbox = obj["bbox"]
                    x1, y1, x2, y2 = bbox
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
