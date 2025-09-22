from deep_sort_realtime.deepsort_tracker import DeepSort

class Tracker:
    def __init__(self, class_names):
        self.tracker = DeepSort(max_age=60, n_init=10, max_cosine_distance=0.1, max_iou_distance=0.9)
        self.class_names = class_names

    def update(self, detections, frame):

        tracks = self.tracker.update_tracks(detections, frame=frame)

        tracked_objects = []
        for track in tracks:
            if not track.is_confirmed():
                continue

            bbox = track.to_tlwh()
            x, y, w, h = map(int, bbox)
            cls_id = track.get_det_class()
            class_name = self.class_names[cls_id]
            track_id = track.track_id

            tracked_objects.append({
                "track_id": track_id,
                "bbox": [x, y, w, h],
                "class": class_name
            })

            return tracked_objects
