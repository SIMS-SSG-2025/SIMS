from device.utils.logger import get_logger
# Initialize logger for inference module
logger = get_logger("Inference")



def run_inference(frame, model):
    try:
        results = model.predict(frame, verbose=False, conf=0.5, iou=0.5)
        res = results[0]

        detections = []
        xywh = res.boxes.xywh
        confs = res.boxes.conf
        cls = res.boxes.cls

        for i in range(len(xywh)):
            x,y,w,h = xywh[i]
            conf = confs[i].item()
            cls_id = int(cls[i].item())
            detections.append(([int(x.item()), int(y.item()), int(w.item()), int(h.item())], conf, cls_id))

        return detections
    except Exception as e:
        logger.error(f"Error in run_inference: {e}")
        return []
