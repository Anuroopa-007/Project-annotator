from PyQt5.QtWidgets import QGraphicsScene, QInputDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QRectF, Qt
from ui.canvas.bbox_item import BBoxItem


class AnnotationScene(QGraphicsScene):
    def __init__(self, annotation_service):
        super().__init__()
        self.annotation_service = annotation_service
        self.start_pos = None
        self.temp_box = None
        self.image_item = None

    def load_image(self, path):
        self.clear()
        self.annotation_service.clear()
        pixmap = QPixmap(path)
        self.image_item = self.addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))


    def mousePressEvent(self, event):
        self.start_pos = event.scenePos()
        self.temp_box = BBoxItem(QRectF(self.start_pos, self.start_pos))
        self.addItem(self.temp_box)

    def mouseMoveEvent(self, event):
        if self.temp_box:
            rect = QRectF(self.start_pos, event.scenePos()).normalized()
            self.temp_box.setRect(rect)

    def mouseReleaseEvent(self, event):
        if not self.temp_box:
            return

        label, ok = QInputDialog.getText(
            None, "Class Label", "Enter class name:"
        )

        if ok and label:
            self.annotation_service.add(label, self.temp_box.rect())
        else:
            self.removeItem(self.temp_box)

        self.temp_box = None
