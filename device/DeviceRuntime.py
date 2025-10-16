import cv2
from ultralytics import YOLO
import time
from device.inference.inference import run_inference
from device.inference.tracker import Tracker, DetectionResults
from device.logic.events import EventManager
import queue
import numpy as np
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
        self.logger = get_logger("DeviceRuntime")
        self.cam = None
        self.running = False
        self.class_names = None
        self.response_queue = queue.Queue()
        self.frame_width = None
        self.frame_height = None
        self._initialize_components()
        self.frame_count = 0
        self.FRAME_SAMPLE = 3
        self.warmup_counter = 0



    def _initialize_components(self):
        self._load_model()

        self.class_names = load_class_mapping("device/training/dataset/yolo11_person_only.yaml")
        ppe_names = load_class_mapping("device/training/dataset/safety-dataset_ppe_only.yaml")

        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            self.logger.error("Failed to open camera")
            raise RuntimeError("Camera initialization failed")

        cam_fps = self.cam.get(cv2.CAP_PROP_FPS)

        ret, frame = self.cam.read()
        if ret:
            self.frame_height, self.frame_width = frame.shape[:2]

        self.tracker = Tracker(class_names=self.class_names, cam_fps=cam_fps)
        inference_logger = get_logger("Inference")
        self.event_manager = EventManager(logger=inference_logger, db_queue=self.db_queue, class_names=self.class_names, ppe_names=ppe_names)

    def start(self):
        self.running = True
        self._update_config()
        prev_time = time.time()
        prev_time_fps = time.time()
        CHECK_INTERVAL = 5
        while self.running:
            try:
                # Capture frame
                ret, frame = self.cam.read()
                if not ret:
                    self.logger.warning("Failed to capture frame from camera")
                    time.sleep(1)
                    continue
                self.frame_count += 1

                if self.warmup_counter < 10:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    detections = run_inference(rgb_frame, self.model)
                    self.event_manager.warmup(frame)
                    self.warmup_counter += 1
                    if self.warmup_counter >= 10:
                        print("Model warmup complete!")
                    continue

                # Process frame
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detections = run_inference(rgb_frame, self.model)
                # Filter detections by class
                trackable_classes = ["Person", "vehicle"]
                detections_for_tracking = [d for d in detections if self.class_names[d[-1]] in trackable_classes]
                results = DetectionResults(detections_for_tracking)

                # Update tracking and handle events
                tracked_objects, in_frame_objects = self.tracker.update(results, rgb_frame)

                if self.frame_count % self.FRAME_SAMPLE == 0:
                    self.event_manager.handle_detections(tracked_objects, rgb_frame, store_obj_pos=True)
                    self.frame_count = 0
                else:
                    self.event_manager.handle_detections(tracked_objects, rgb_frame, store_obj_pos=False)


                # Calculate and display FPS
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

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                continue


    def stop(self):
        # Stop and clean up the device runtime components
        self.running = False
        if self.cam:
            self.cam.release()
        self.db_queue.put({"action": "set_status", "status": False})
        cv2.destroyAllWindows()


    def _check_status(self):
        self.db_queue.put({"action": "get_status", "response": self.response_queue})
        try:
            run_flag = self.response_queue.get_nowait()
            if run_flag is False:
                self.running = False

        except queue.Empty:
            pass

    def _load_model(self):
        model_config = "device/training/models/yolo11_ppe_cfg.yaml"
        model_path = "device/training/models/yolo11_person_only.pt"

        try:
            self.model = YOLO(model_path)



        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise

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

        zones = self.event_manager.get_zones_coords()
        for zone in zones:
            pts = np.array(zone, np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 0, 255), thickness=2)

        cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Camera feed", frame)



    def _update_config(self):
        self.db_queue.put({"action": "get_zones", "response": self.response_queue})
        try:
            zones = self.response_queue.get(timeout=0.1)
            print(f"Fetched {len(zones)} zones from database.")
            self.event_manager.set_zones(zones, self.frame_width, self.frame_height)

        except queue.Empty:
            print("No zones fetched.")
        self.db_queue.put({"action": "get_latest_object_id", "response": self.response_queue})
        try:
            last_object_id = self.response_queue.get(timeout=0.1)
            self.tracker.set_track_id(last_object_id)

        except queue.Empty:
            print("No objects fetched.")

        self.db_queue.put({"action": "get_location_id", "response": self.response_queue})
        try:
            location_id = self.response_queue.get(timeout=0.1)
            self.event_manager.set_location(location_id)
        except queue.Empty:
            print("No location ID fetched.")

    """
    # Update the configuration if needed
    # get zones from db
    # pass them into eventhandler
    """
