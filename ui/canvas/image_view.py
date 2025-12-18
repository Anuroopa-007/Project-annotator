from PyQt5.QtWidgets import QGraphicsView
# from ui.canvas.scene import AnnotationScene
from ui.canvas.annotation_scene import AnnotationScene


class ImageView(QGraphicsView):
    def __init__(self, annotation_service):
        super().__init__()
        self.image_path = None
        self.scene = AnnotationScene(annotation_service)
        self.setScene(self.scene)
        self.setMouseTracking(True)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def load_image(self, path):
        self.image_path = path
        self.scene.load_image(path)

    def wheelEvent(self, event):
        zoom = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom, zoom)
