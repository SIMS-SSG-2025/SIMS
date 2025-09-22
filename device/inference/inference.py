
def run_inference(frame, model):
    results = model.predict(frame, conf=0.8, verbose=False)
    detections = []

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()

        for box, score, cls in zip(boxes, scores, class_ids):
            x1, y1, x2, y2 = box
            detections.append(([x1, y1, x2-x1, y2-y1], score, cls))

    return detections
