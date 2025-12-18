from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QMessageBox, QFileDialog
)
from ui.canvas.image_view import ImageView
from ui.sidebar import Sidebar
from services.annotation_service import AnnotationService
from formats.yolo import YOLOExporter
from services.auto_annotate_service import AutoAnnotateService
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CV Annotator")
        self.resize(1400, 900)

        self.current_model_path = "models/pretrained/yolov8n.pt"
        self.image_paths = []
        self.current_image_index = 0

        # Services
        self.annotation_service = AnnotationService()
        self.image_view = ImageView(self.annotation_service)

        # Layout
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = Sidebar(self)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.image_view)

        self.setCentralWidget(central)

    # ------------------------
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.jpg *.png *.jpeg *.bmp)"
        )
        if path:
            self.annotation_service.clear()
            self.image_view.load_image(path)
            self.sidebar.set_status(f"Loaded: {os.path.basename(path)}")

    # ------------------------
    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return

        exts = ('.jpg', '.jpeg', '.png', '.bmp')
        self.image_paths = sorted([
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(exts)
        ])

        if not self.image_paths:
            QMessageBox.warning(self, "Empty", "No images found")
            return

        self.sidebar.populate_images(self.image_paths)
        self.current_image_index = 0
        self.load_image_from_list(self.image_paths[0])
        self.sidebar.set_status(f"{len(self.image_paths)} images loaded")

    # ------------------------
    def load_image_from_list(self, path):
        # Auto-save previous image
        if self.annotation_service.annotations:
            YOLOExporter.export(
                image_path=self.image_view.image_path,
                annotations=self.annotation_service.annotations
            )

        self.annotation_service.clear()
        self.image_view.load_image(path)
        self.sidebar.set_status(f"Loaded: {os.path.basename(path)}")

    # ------------------------
    def save_yolo(self):
        if not self.image_view.image_path:
            QMessageBox.warning(self, "Error", "No image loaded")
            return

        if not self.annotation_service.annotations:
            QMessageBox.warning(self, "Error", "No annotations to save")
            return

        YOLOExporter.export(
            image_path=self.image_view.image_path,
            annotations=self.annotation_service.annotations
        )

        self.sidebar.set_status("YOLO saved ✔")

    # ------------------------
    def auto_annotate(self):
        if not self.image_view.image_path:
            QMessageBox.warning(self, "Error", "Load image first")
            return

        service = AutoAnnotateService(self.current_model_path)
        predictions = service.predict(self.image_view.image_path, conf=0.25)

        self.image_view.scene.add_auto_boxes(predictions)
        self.sidebar.set_status(f"Auto: {len(predictions)} objects")

    # ------------------------
    def on_model_changed(self, text):
        if "yolov8n" in text:
            self.current_model_path = "models/pretrained/yolov8n.pt"
        elif "yolov8s" in text:
            self.current_model_path = "models/pretrained/yolov8s.pt"
        elif "yolov8m" in text:
            self.current_model_path = "models/pretrained/yolov8m.pt"

    # ------------------------
    def export_dataset(self):
        QMessageBox.information(
            self,
            "Export",
            "Dataset export coming soon (YOLO / COCO / VOC)"
        )
