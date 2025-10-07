import cv2
from ultralytics import YOLO
import time

from device.inference.inference import run_inference
from device.inference.tracker import Tracker, DetectionResults
from device.logic.events import EventManager
import queue

import yaml
from ultralytics.nn.tasks import DetectionModel
import torch
from .utils.logger import get_logger
from device.training.dataset.dataset_transform import load_class_mapping

class DeviceRuntime:
    def __init__(self, db_queue):
        self.db_queue = db_queue
        self.tracker = None
        self.event_manager = None
        self.model = None
        self.logger = None
        self.cam = None
        self.running = False
        self.class_names = None
        self.response_queue = queue.Queue()
        self._initialize_components()



    def _initialize_components(self):
        self._load_model()

        self.class_names = load_class_mapping("device/training/dataset/safety_dataset_filtered.yaml")

        self.cam = cv2.VideoCapture(0)
        cam_fps = self.cam.get(cv2.CAP_PROP_FPS)

        self.tracker = Tracker(class_names=self.class_names, cam_fps=cam_fps)
        self.logger = get_logger("Inference")
        self.event_manager = EventManager(logger=self.logger, db_queue=self.db_queue, class_names=self.class_names)

    def start(self):
        self.running = True
        self._update_config()
        prev_time = time.time()
        prev_time_fps = time.time()
        CHECK_INTERVAL = 5
        while self.running:
            # check for stop signal
            ret, frame = self.cam.read()
            if not ret:
                continue
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detections = run_inference(rgb_frame, self.model)
            trackable_classes = ["Person", "vehicle"]
            ppe_classes = ["Hardhat", "NO-Hardhat", "Safety Vest", "NO-Safety Vest"]
            detections_for_tracking = [d for d in detections if self.class_names[d[-1]] in trackable_classes]
            results = DetectionResults(detections_for_tracking)
            ppe_detections = [d for d in detections if self.class_names[d[-1]] in ppe_classes]
            tracked_objects, in_frame_objects = self.tracker.update(results, frame)
            self.event_manager.handle_detections(tracked_objects, ppe_detections)
            current_time = time.time()
            fps = 1 / (current_time - prev_time_fps)
            prev_time_fps = current_time
            self._visualize(in_frame_objects, frame, fps)

            # Periodically check DB for stop flag
            now = time.time()
            if now - prev_time > CHECK_INTERVAL:
                self._check_status()
                prev_time = now

            if cv2.waitKey(1) == ord('q'):
                self.stop()
                break


    def stop(self):
        # Stop and clean up the device runtime components
        self.running = False
        if self.cam:
            self.cam.release()

        cv2.destroyAllWindows()


    def _check_status(self):
        self.db_queue.put({"action": "get_status", "response": self.response_queue})
        print("Checking Run Status")
        try:
            run_flag = self.response_queue.get_nowait()
            if run_flag is False:
                self.running = False

        except queue.Empty:
            pass

    def _load_model(self):
        model_config = "device/training/models/yolo11_ppe_cfg.yaml"
        model_path = "device/training/models/yolo_ppe.pth"
        with open(model_config, 'r') as file:
            model_config = yaml.safe_load(file)


        num_classes = model_config["nc"]
        self.model = DetectionModel(cfg=model_config, nc=num_classes)
        self.model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage))
        self.model.eval()

    def _visualize(self, tracked_objects, frame, fps):
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


        cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Camera feed", frame)



    def _update_config(self):
        # Update the configuration if needed
        # get zones from db
        # pass them into eventhandler
        pass
