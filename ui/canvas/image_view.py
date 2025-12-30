# ui/canvas/image_view.py - FINAL FIXED: Rectangle drag works + Polygon mode perfect
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QWheelEvent

from ui.canvas.annotation_scene import AnnotationScene


class ImageView(QGraphicsView):
    def __init__(self, annotation_service):
        super().__init__()
        self.image_path = None
        self.scene = AnnotationScene(annotation_service)
        self.zoom_level = 0

        self.setScene(self.scene)

        # CRITICAL: Always allow mouse events to reach scene
        self.setDragMode(QGraphicsView.NoDrag)  # ← Don't use ScrollHandDrag — it interferes!
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(0)

        # Allow panning by middle mouse drag
        self.setInteractive(True)

    def load_image(self, path):
        self.image_path = path
        self.scene.load_image(path)
        self.reset_zoom()

    # =========================================================
    # ZOOM (Only active when NOT drawing polygon)
    # =========================================================
    def wheelEvent(self, event: QWheelEvent):
        # Block zoom only while actively adding polygon points
        if (hasattr(self.scene, 'is_polygon_mode') and 
            self.scene.is_polygon_mode and 
            len(self.scene.polygon_points) > 0):
            return

        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.scale(1.25, 1.25)
        self.zoom_level += 1

    def zoom_out(self):
        self.scale(0.8, 0.8)
        self.zoom_level -= 1

    def reset_zoom(self):
        self.resetTransform()
        self.zoom_level = 0

    # =========================================================
    # MOUSE DRAG FOR PANNING (Middle mouse)
    # =========================================================
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MiddleButton:
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    # =========================================================
    # POLYGON MODE (Just notify scene)
    # =========================================================
    def set_polygon_mode(self, enabled: bool):
        self.scene.set_polygon_mode(enabled)