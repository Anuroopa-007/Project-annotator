from PyQt5.QtWidgets import QGraphicsScene, QInputDialog
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPixmap, QImage
from ui.canvas.bbox_item import BBoxItem
from PyQt5.QtWidgets import QGraphicsTextItem

from utils.colors import get_color
import os


class AnnotationScene(QGraphicsScene):
    def __init__(self, annotation_service):
        super().__init__()
        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.annotation_service = annotation_service
        self.image_item = None
        self.image_path = None
        self.start_pos = None
        self.temp_rect = None

    # -----------------------------
    # def mousePressEvent(self, event):
    #     if event.button() == Qt.LeftButton:
    #         self.start_pos = event.scenePos()
    #         self.temp_rect = self.addRect(QRectF(), pen=Qt.red)
    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())

    # If click on label text → redirect to parent box
        if isinstance(item, QGraphicsTextItem) and isinstance(item.parentItem(), BBoxItem):
            item = item.parentItem()

    # Click on existing box → let Qt select it
        if isinstance(item, BBoxItem):
            self.clearFocus() 
            self.clearSelection() 
            item.setSelected(True)
            event.accept()
            return

    # Click empty area → start drawing new box
        if event.button() == Qt.LeftButton:
            self.clearSelection()
           # clears selection correctly
            self.start_pos = event.scenePos()
            self.temp_rect = self.addRect(QRectF(), pen=Qt.red)
            event.accept()


    # def mousePressEvent(self, event):
    #     item = self.itemAt(event.scenePos(), self.views()[0].transform())

    # # 🟦 Click on existing box → SELECT it
    #     if isinstance(item, BBoxItem):
    #         super().mousePressEvent(event)
    #         return

    # # ➕ Click empty area → draw new box
    #     if event.button() == Qt.LeftButton:
    #         self.start_pos = event.scenePos()
    #         self.temp_rect = self.addRect(QRectF(), pen=Qt.red)


    def mouseMoveEvent(self, event):
        if self.temp_rect:
            rect = QRectF(self.start_pos, event.scenePos()).normalized()
            self.temp_rect.setRect(rect)

    

    def mouseReleaseEvent(self, event):
        if not self.temp_rect:
            return

        rect = self.temp_rect.rect()
        self.removeItem(self.temp_rect)
        self.temp_rect = None

        if rect.width() < 10 or rect.height() < 10:
            return

        label, ok = QInputDialog.getText(
            None, "Object Name", "Enter object name:"
        )

        if ok and label.strip():
            bbox = BBoxItem(rect, label)
            self.addItem(bbox)
            self.annotation_service.add(label, rect)

    # -----------------------------
    # IMAGE MODE
    def load_image(self, path):
        pixmap = QPixmap(path)
        self.clear()
        self.image_item = self.addPixmap(pixmap)
        self.image_path = path
        self.setSceneRect(QRectF(pixmap.rect()))
        self.annotation_service.clear()

    # -----------------------------
    # VIDEO MODE (IMPORTANT)
    def set_video_frame(self, qimage: QImage):
        pixmap = QPixmap.fromImage(qimage)

        if self.image_item is None:
            self.image_item = self.addPixmap(pixmap)
        else:
            self.image_item.setPixmap(pixmap)

        self.setSceneRect(QRectF(pixmap.rect()))

    # -----------------------------
    def clear_annotations(self):
        for item in self.items():
            if isinstance(item, BBoxItem):
                self.removeItem(item)
        self.annotation_service.clear()

    # -----------------------------
    def add_auto_boxes(self, predictions):
        if not self.image_item:
            return

        img_w = self.image_item.pixmap().width()
        img_h = self.image_item.pixmap().height()

        for label, x_center, y_center, w_norm, h_norm in predictions:
            x = (x_center - w_norm / 2) * img_w
            y = (y_center - h_norm / 2) * img_h
            w = w_norm * img_w
            h = h_norm * img_h

            rect = QRectF(x, y, w, h)
            bbox = BBoxItem(rect, label)
            self.addItem(bbox)
            self.annotation_service.add(label, rect)
