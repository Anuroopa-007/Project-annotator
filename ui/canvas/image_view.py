from PyQt5.QtWidgets import QGraphicsView
# from ui.canvas.scene import AnnotationScene
from ui.canvas.annotation_scene import AnnotationScene

class ImageView(QGraphicsView):
    def __init__(self, annotation_service):
        super().__init__()
        self.image_path = None
        self.scene = AnnotationScene(annotation_service)
        self.setScene(self.scene)

        # ✅ ADD THESE
        self.setDragMode(QGraphicsView.ScrollHandDrag)   # PAN
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoom_level = 0

    def load_image(self, path):
        self.image_path = path
        self.scene.load_image(path)
        self.reset_zoom()  # ✅ reset zoom when loading new image

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # ✅ ADD THESE METHODS
    def zoom_in(self):
        self.scale(1.25, 1.25)
        self.zoom_level += 1

    def zoom_out(self):
        self.scale(0.8, 0.8)
        self.zoom_level -= 1

    def reset_zoom(self):
        self.resetTransform()
        self.zoom_level = 0
