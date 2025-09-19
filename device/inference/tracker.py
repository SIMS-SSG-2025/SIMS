from deep_sort_realtime.deepsort_tracker import DeepSort

class Tracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=500, n_init=20, max_cosine_distance=0.1, max_iou_distance=0.9)

    def update(self, detections, frame):
        dets_for_tracker = [(det["bbox"], det["confidence"], det["object_type"]) for det in detections]

        tracks = self.tracker.update_tracks(dets_for_tracker, frame=frame)

        tracked_objects = []
        for track in tracks:
            if not track.is_confirmed():
                continue

            bbox = track.to_tlwh()
            x, y, w, h = map(int, bbox)
            cls_id = track.get_det_class()
            track_id = track.track_id

            tracked_objects.append({
                "track_id": track_id,
                "bbox": [x, y, w, h],
                "class_id": cls_id
            })

            return tracked_objects
