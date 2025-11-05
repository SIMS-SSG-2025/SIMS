# Convert pytorch .pt models to TensorRT using ultralytics trt: model.export

from ultralytics import YOLO

MODEL_PATH = "./models/yolo11_ppe_mendelay.pt" # PPE detection model
# MODEL_PATH = "yolo11n-cls.pt" # ReID module for botsort
# MODEL_PATH = "./models/yolo11_person_only.pt" # Person detection model

model = YOLO(MODEL_PATH)

model.export(format="engine", half=True, dynamic=True, device=0) # PPE
# model.export(format="engine", half=True, dynamic=True, batch=8, device=0) # ReID
# model.export(format="engine", half=True, device=0) # Person

