from PyQt5.QtWidgets import QGraphicsScene, QInputDialog
from PyQt5.QtCore import QRectF, Qt
from ui.canvas.bbox_item import BBoxItem
import os


class AnnotationScene(QGraphicsScene):
    def __init__(self, annotation_service):
        super().__init__()
        self.annotation_service = annotation_service
        self.image_item = None
        self.image_path = None
        self.start_pos = None
        self.temp_rect = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.scenePos()
            self.temp_rect = self.addRect(QRectF(), pen=Qt.red)

    # -----------------------------
    def mouseMoveEvent(self, event):
        if self.temp_rect:
            rect = QRectF(self.start_pos, event.scenePos()).normalized()
            self.temp_rect.setRect(rect)

    # -----------------------------
    def mouseReleaseEvent(self, event):
        if not self.temp_rect:
            return

        rect = self.temp_rect.rect()
        self.removeItem(self.temp_rect)
        self.temp_rect = None

        if rect.width() < 10 or rect.height() < 10:
            return

        # 🔹 Ask object name
        label, ok = QInputDialog.getText(
            None, "Object Name", "Enter object name:"
        )

        if ok and label.strip():
            bbox = BBoxItem(rect, label)
            self.addItem(bbox)
            self.annotation_service.add(label, rect)

    # -----------------------------
    def load_image(self, path):
        from PyQt5.QtGui import QPixmap
        pixmap = QPixmap(path)
        self.image_item = self.addPixmap(pixmap)
        self.image_path = path
        self.setSceneRect(QRectF(pixmap.rect()))
        self.clear_annotations()

    # -----------------------------
    def clear_annotations(self):
        # Remove all BBoxItem, keep image
        for item in self.items():
            if isinstance(item, BBoxItem):
                self.removeItem(item)
        self.annotation_service.clear()

    # -----------------------------
    def save_yolo(self):
        if not self.image_item or not self.image_path:
            return

        img_w = self.image_item.pixmap().width()
        img_h = self.image_item.pixmap().height()

        label_path = os.path.splitext(self.image_path)[0] + ".txt"

        class_map = {}
        lines = []
        for item in self.items():
            if isinstance(item, BBoxItem):
                cls_id, x, y, w, h = item.to_yolo(img_w, img_h, class_map)
                lines.append(f"{cls_id} {x} {y} {w} {h}")

        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        with open(label_path, "w") as f:
            f.write("\n".join(lines))

        print(f"Saved YOLO labels → {label_path}")

    # -----------------------------
    def add_auto_boxes(self, predictions):
        """
        predictions: [(label, x_center, y_center, w, h)] in normalized YOLO format
        """
        if not self.image_item:
            return

        img_w = self.image_item.pixmap().width()
        img_h = self.image_item.pixmap().height()

        for label, x_center, y_center, w_norm, h_norm in predictions:
            # Convert normalized coordinates back to scene (pixel) coordinates
            x = (x_center - w_norm / 2) * img_w
            y = (y_center - h_norm / 2) * img_h
            w = w_norm * img_w
            h = h_norm * img_h

            rect = QRectF(x, y, w, h)
            bbox = BBoxItem(rect, label)
            self.addItem(bbox)
            self.annotation_service.add(label, rect)
