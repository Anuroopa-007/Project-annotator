# ui/canvas/annotation_scene.py - FINAL FIXED & STABLE
from PyQt5.QtWidgets import (
    QGraphicsScene, QGraphicsPolygonItem, QGraphicsEllipseItem,
    QInputDialog
)
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QPolygonF
from ui.canvas.bbox_item import BBoxItem
from utils.colors import get_color


class AnnotationScene(QGraphicsScene):
    def __init__(self, annotation_service, parent=None):
        super().__init__(parent)
        self.annotation_service = annotation_service
        self.image_item = None
        self.image_path = None
        self.polygon_points = []
        self.current_polygon = None
        self.is_polygon_mode = False

    def set_polygon_mode(self, enabled: bool):
        self.is_polygon_mode = enabled
        if not enabled and self.current_polygon:
            # Cancel unfinished polygon
            self.removeItem(self.current_polygon)
            self.reset_polygon()

    def mousePressEvent(self, event):
        pos = event.scenePos()

        # Click on existing item → select it
        item = self.itemAt(pos, self.views()[0].transform())
        if item and (isinstance(item, BBoxItem) or isinstance(item, QGraphicsPolygonItem)):
            self.clearSelection()
            item.setSelected(True)
            return

        if self.is_polygon_mode:
            if event.button() == Qt.LeftButton:
                self.polygon_points.append(pos)

                # Create new polygon item if needed
                if self.current_polygon is None or self.current_polygon.scene() is None:
                    self.current_polygon = QGraphicsPolygonItem()
                    pen = QPen(QColor(255, 100, 0), 3)
                    self.current_polygon.setPen(pen)
                    self.current_polygon.setBrush(QBrush(QColor(255, 100, 0, 50)))
                    self.addItem(self.current_polygon)

                # Update polygon
                poly = QPolygonF(self.polygon_points)
                self.current_polygon.setPolygon(poly)

            elif event.button() == Qt.RightButton:
                self.finish_polygon()

        else:
            # Rectangle mode
            if event.button() == Qt.LeftButton:
                self.clearSelection()
                self.start_pos = pos
                self.temp_rect = self.addRect(QRectF(pos, pos), QPen(QColor(255, 100, 0), 2))

    def mouseMoveEvent(self, event):
        if not self.is_polygon_mode and hasattr(self, 'temp_rect') and self.temp_rect:
            rect = QRectF(self.start_pos, event.scenePos()).normalized()
            self.temp_rect.setRect(rect)

    def mouseReleaseEvent(self, event):
        if not self.is_polygon_mode and hasattr(self, 'temp_rect') and self.temp_rect:
            rect = self.temp_rect.rect().normalized()
            self.removeItem(self.temp_rect)
            del self.temp_rect

            if rect.width() < 10 or rect.height() < 10:
                return

            label, ok = QInputDialog.getText(None, "Label", "Enter object name:")
            if ok and label.strip():
                bbox = BBoxItem(rect, label.strip())
                self.addItem(bbox)
                self.annotation_service.add(label.strip(), rect)

    def finish_polygon(self):
        if len(self.polygon_points) < 3 or not self.current_polygon:
            self.reset_polygon()
            return

        label, ok = QInputDialog.getText(None, "Label", "Enter object name:")
        if not (ok and label.strip()):
            self.reset_polygon()
            return

        # Finalize appearance
        color = get_color(label.strip())
        pen = QPen(color, 3)
        self.current_polygon.setPen(pen)
        self.current_polygon.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 80)))

        # Add draggable grip points
        for i, point in enumerate(self.polygon_points):
            grip = QGraphicsEllipseItem(-8, -8, 16, 16, self.current_polygon)
            grip.setPos(point)
            grip.setBrush(QBrush(QColor("white")))
            grip.setPen(QPen(QColor("orange"), 2))
            grip.setFlag(QGraphicsEllipseItem.ItemIsMovable)
            grip.setCursor(Qt.SizeAllCursor)

            def make_grip_moved(poly=self.current_polygon, idx=i):
                def moved():
                    points = list(poly.polygon())
                    points[idx] = grip.pos()
                    poly.setPolygon(QPolygonF(points))
                return moved

            grip.itemChange = lambda change, value, f=make_grip_moved(): \
                f() if change == QGraphicsEllipseItem.ItemPositionHasChanged else value

        # Save bounding box for YOLO
        bbox_rect = self.current_polygon.boundingRect()
        self.annotation_service.add(label.strip(), bbox_rect)

        self.reset_polygon()

    def reset_polygon(self):
        if self.current_polygon and self.current_polygon.scene():
            self.removeItem(self.current_polygon)
        self.polygon_points = []
        self.current_polygon = None

    # ---------------- IMAGE & VIDEO ----------------
    def load_image(self, path):
        pixmap = QPixmap(path)
        self.clear()
        self.image_item = self.addPixmap(pixmap)
        self.image_path = path
        self.setSceneRect(QRectF(pixmap.rect()))
        self.annotation_service.clear()

    def set_video_frame(self, qimage: QImage):
        pixmap = QPixmap.fromImage(qimage)
        if self.image_item is None:
            self.image_item = self.addPixmap(pixmap)
        else:
            self.image_item.setPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))

    def clear_annotations(self):
        for item in self.items():
            if isinstance(item, (BBoxItem, QGraphicsPolygonItem)):
                self.removeItem(item)
        self.annotation_service.clear()

    def add_auto_boxes(self, predictions, track_ids=None):
        if not self.image_item:
            return

        img_w = self.image_item.pixmap().width()
        img_h = self.image_item.pixmap().height()

        for i, (label, x_center, y_center, w_norm, h_norm) in enumerate(predictions):
            x = (x_center - w_norm / 2) * img_w
            y = (y_center - h_norm / 2) * img_h
            w = w_norm * img_w
            h = h_norm * img_h

            rect = QRectF(x, y, w, h)
            track_id = track_ids[i] if track_ids else None
            display_label = f"{label} #{track_id}" if track_id is not None else label

            bbox = BBoxItem(rect, display_label)
            self.addItem(bbox)
            self.annotation_service.add(label, rect)