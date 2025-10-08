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
        self.logger = get_logger("DeviceRuntime")
        self.cam = None
        self.running = False
        self.class_names = None
        self.response_queue = queue.Queue()
        
        self.logger.info("Initializing DeviceRuntime")
        self._initialize_components()
        self.logger.info("DeviceRuntime initialization complete")



    def _initialize_components(self):
        self.logger.info("Loading AI model...")
        self._load_model()
        self.logger.info("AI model loaded successfully")

        self.logger.info("Loading class mappings...")
        self.class_names = load_class_mapping("device/training/dataset/safety_dataset_filtered.yaml")
        self.logger.info(f"Loaded {len(self.class_names)} classes: {list(self.class_names.values())}")

        self.logger.info("Initializing camera...")
        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            self.logger.error("Failed to open camera")
            raise RuntimeError("Camera initialization failed")
        
        cam_fps = self.cam.get(cv2.CAP_PROP_FPS)
        self.logger.info(f"Camera initialized - FPS: {cam_fps}")

        self.logger.info("Initializing tracker and event manager...")
        self.tracker = Tracker(class_names=self.class_names, cam_fps=cam_fps)
        inference_logger = get_logger("Inference")
        self.event_manager = EventManager(logger=inference_logger, db_queue=self.db_queue, class_names=self.class_names)
        self.logger.info("All components initialized successfully")

    def start(self):
        self.logger.info("Starting device runtime monitoring")
        self.running = True
        self._update_config()
        
        prev_time = time.time()
        prev_time_fps = time.time()
        CHECK_INTERVAL = 5
        frame_count = 0
        detection_count = 0
        
        while self.running:
            try:
                # Capture frame
                ret, frame = self.cam.read()
                if not ret:
                    self.logger.warning("Failed to capture frame from camera")
                    continue
                    
                frame_count += 1
                
                # Process frame
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detections = run_inference(rgb_frame, self.model)
                
                if detections:
                    detection_count += len(detections)
                    self.logger.debug(f"Frame {frame_count}: Found {len(detections)} detections")
                
                # Filter detections by class
                trackable_classes = ["Person", "vehicle"]
                ppe_classes = ["Hardhat", "NO-Hardhat", "Safety Vest", "NO-Safety Vest"]
                detections_for_tracking = [d for d in detections if self.class_names[d[-1]] in trackable_classes]
                results = DetectionResults(detections_for_tracking)
                ppe_detections = [d for d in detections if self.class_names[d[-1]] in ppe_classes]
                
                # Update tracking and handle events
                tracked_objects, in_frame_objects = self.tracker.update(results, frame)
                if tracked_objects:
                    self.logger.debug(f"Tracking {len(tracked_objects)} objects")
                
                self.event_manager.handle_detections(tracked_objects, ppe_detections)
                
                # Calculate and display FPS
                current_time = time.time()
                fps = 1 / (current_time - prev_time_fps)
                prev_time_fps = current_time
                self._visualize(in_frame_objects, frame, fps)

                # Periodically check DB for stop flag and log stats
                now = time.time()
                if now - prev_time > CHECK_INTERVAL:
                    self.logger.info(f"Processing stats: {frame_count} frames, {detection_count} total detections, {fps:.1f} FPS")
                    self._check_status()
                    prev_time = now

                if cv2.waitKey(1) == ord('q'):
                    self.logger.info("Quit key pressed - stopping monitoring")
                    self.stop()
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                continue
                
        self.logger.info(f"Monitoring stopped. Total: {frame_count} frames processed, {detection_count} detections")


    def stop(self):
        # Stop and clean up the device runtime components
        self.logger.info("Stopping device runtime")
        self.running = False
        if self.cam:
            self.cam.release()
            self.logger.info("Camera released")

        cv2.destroyAllWindows()
        self.logger.info("Device runtime stopped successfully")


    def _check_status(self):
        self.db_queue.put({"action": "get_status", "response": self.response_queue})
        self.logger.debug("Checking system run status")
        try:
            run_flag = self.response_queue.get_nowait()
            if run_flag is False:
                self.logger.info("System stop signal received")
                self.running = False
            else:
                self.logger.debug("System continues running")

        except queue.Empty:
            self.logger.warning("No response received for status check")
            pass

    def _load_model(self):
        model_config = "device/training/models/yolo11_ppe_cfg.yaml"
        model_path = "device/training/models/yolo_ppe.pth"
        
        try:
            self.logger.info(f"Loading model configuration from: {model_config}")
            with open(model_config, 'r') as file:
                model_config = yaml.safe_load(file)

            num_classes = model_config["nc"]
            self.logger.info(f"Model configuration loaded - {num_classes} classes")
            
            self.logger.info(f"Loading model weights from: {model_path}")
            self.model = DetectionModel(cfg=model_config, nc=num_classes)
            self.model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage))
            self.model.eval()
            self.logger.info("Model loaded and set to evaluation mode")
            
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

        
        cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Camera feed", frame)



    def _update_config(self):
        self.db_queue.put({"action": "get_zones", "response": self.response_queue})
        try:
            zones = self.response_queue.get(timeout=0.1)
            print(f"fetched {len(zones)} zones from database.")
            self.event_manager.set_zones(zones)

        except queue.Empty:
            print("No zones fetched.")


    """
    # Update the configuration if needed
    # get zones from db
    # pass them into eventhandler
    """
