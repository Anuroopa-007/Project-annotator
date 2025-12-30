# ui/canvas/image_view.py - FINAL VERSION (No Shaking + Smart Polygon Support)
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

        # Initial settings
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # Allow panning by dragging
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # Zoom at cursor
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(0)  # Remove border

    def load_image(self, path):
        self.image_path = path
        self.scene.load_image(path)
        self.reset_zoom()  # Always start at 100% when loading new image

    # =========================================================
    # ZOOM CONTROLS
    # =========================================================
    def wheelEvent(self, event: QWheelEvent):
        # Only allow zoom if NOT in polygon mode
        if hasattr(self.scene, 'is_polygon_mode') and self.scene.is_polygon_mode:
            return  # Disable zoom during polygon drawing

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
    # POLYGON MODE SUPPORT (Prevents pan/zoom conflicts)
    # =========================================================
    def set_polygon_mode(self, enabled: bool):
        """Call this from MainWindow when toggling polygon mode"""
        self.scene.set_polygon_mode(enabled)

        if enabled:
            # Disable panning and zooming while drawing polygon
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            # Re-enable normal panning
            self.setDragMode(QGraphicsView.ScrollHandDrag)