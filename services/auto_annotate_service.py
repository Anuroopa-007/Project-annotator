

# ACTIVE_MODEL = "models/pretrained/yolov8n.pt"

# def auto_annotate(image_path, scene):
#     from ultralytics import YOLO
#     model = YOLO(ACTIVE_MODEL)
#     results = model(image_path)[0]

#     for box in results.boxes:
#         x1, y1, x2, y2 = box.xyxy[0].tolist()
#         cls = int(box.cls[0])

#         scene.add_bbox(
#             x1, y1,
#             x2 - x1,
#             y2 - y1,
#             cls
#         )
from ultralytics import YOLO


class AutoAnnotateService:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.class_names = self.model.names  # {0: 'person', 1: 'car', ...}

    def predict(self, image_path, conf=0.25):
        """
        Returns:
        [
          (label, x, y, w, h)   # normalized YOLO format
        ]
        """
        results = self.model(image_path, conf=conf)[0]

        predictions = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = self.class_names[cls_id]

            x, y, w, h = box.xywhn[0].tolist()  # normalized
            predictions.append((label, x, y, w, h))

        return predictions
