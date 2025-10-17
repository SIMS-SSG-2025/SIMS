from device.utils.logger import get_logger
import numpy as np
logger = get_logger("Inference")



def run_inference(frame, model, conf=0.5, iou=0.5):
    try:
        results = model.predict(frame, verbose=False, conf=conf, iou=iou)
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




def run_inference_roi(frame, bbox, model):
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox

    bw, bh = x2 - x1, y2 - y1
    if bw <= 0 or bh <= 0:
        return []

    bbox_area_ratio = (bw * bh) / (frame.shape[0] * frame.shape[1])

    k = 40  # steepness: higher = sharper transition
    x0 = 0.008  # midpoint (area ratio where transition starts)
    max_expand = 3
    min_expand = 0.5
    expand_ratio = min_expand + (max_expand - min_expand) / (1 + np.exp(k * (bbox_area_ratio - x0)))

    expand_x = int(bh * expand_ratio)
    expand_y = int(bw * expand_ratio)

    x1_exp = max(0, x1 - expand_x)
    y1_exp = max(0, y1 - expand_y)
    x2_exp = min(w, x2 + expand_x)
    y2_exp = min(h, y2 + expand_y)

    roi = frame[y1_exp:y2_exp, x1_exp:x2_exp]

    roi_detections = run_inference(roi, model, conf=0.3, iou=0.5)

    # Map back to frame coordinates
    detections = []
    for det in roi_detections:
        (cx, cy, bw, bh), conf, cls = det

        cx_global = cx + x1_exp
        cy_global = cy + y1_exp

        detections.append([
            (cx_global, cy_global, bw, bh),
            conf,
            cls
        ])

    return detections