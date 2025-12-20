# main_window.py
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QFileDialog
)

from ui.canvas.image_view import ImageView
from ui.sidebar import Sidebar
from ui.topbar import TopBar  # Import the new TopBar
from services.annotation_service import AnnotationService
from formats.yolo import YOLOExporter
from services.auto_annotate_service import AutoAnnotateService
from services.dataset_service import create_data_yaml
from services.training_service import train_yolo
from services.export_service import export_yolo_dataset



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CV Annotator")
        self.resize(1600, 900)

        self.current_model_path = "models/pretrained/yolov8n.pt"
        self.image_paths = []
        self.current_image_index = 0

        # Services
        self.annotation_service = AnnotationService()
        self.image_view = ImageView(self.annotation_service)

        # === MAIN LAYOUT WITH TOPBAR ===
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Add TopBar at the top
        self.topbar = TopBar(self)
        main_layout.addWidget(self.topbar)

        # 2. Content area: Sidebar (left) + Image View (right)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.image_view, stretch=1)  # Image view takes most space

        main_layout.addLayout(content_layout)

        # Set the central widget
        self.setCentralWidget(central_widget)

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

        exts = (".jpg", ".jpeg", ".png", ".bmp")
        self.image_paths = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(exts)
        )

        if not self.image_paths:
            QMessageBox.warning(self, "Empty", "No images found")
            return

        self.sidebar.populate_images(self.image_paths)
        self.current_image_index = 0
        self.load_image_from_list(self.image_paths[0])
        self.sidebar.set_status(f"{len(self.image_paths)} images loaded")

    # ------------------------
    def load_image_from_list(self, path):
        # Auto-save previous image annotations
        if self.annotation_service.annotations and hasattr(self.image_view, 'image_path') and self.image_view.image_path:
            YOLOExporter.export(
                image_path=self.image_view.image_path,
                annotations=self.annotation_service.annotations,
                dataset_path="storage/datasets/default"
            )

        self.annotation_service.clear()
        self.image_view.load_image(path)
        self.sidebar.set_status(f"Loaded: {os.path.basename(path)}")
        self.sidebar.highlight_current_image(path)

    # ------------------------
    def save_yolo(self):
        if not hasattr(self.image_view, 'image_path') or not self.image_view.image_path:
            QMessageBox.warning(self, "Error", "No image loaded")
            return

        if not self.annotation_service.annotations:
            QMessageBox.warning(self, "Error", "No annotations to save")
            return

        YOLOExporter.export(
            image_path=self.image_view.image_path,
            annotations=self.annotation_service.annotations,
            dataset_path="storage/datasets/default",
            split="train"
        )

        create_data_yaml("storage/datasets/default")
        self.sidebar.set_status("YOLO saved")

    # ------------------------
    def auto_annotate(self):
        if not hasattr(self.image_view, 'image_path') or not self.image_view.image_path:
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
    def train_model(self):
        dataset_path = "storage/datasets/default"
        data_yaml = f"{dataset_path}/data.yaml"

        if not os.path.exists(data_yaml):
            QMessageBox.warning(
                self,
                "Missing data.yaml",
                "Please save YOLO annotations first."
            )
            return

        QMessageBox.information(
            self,
            "Training Started",
            "Training has started.\nThis may take several minutes.\nCheck terminal logs."
        )

        train_yolo(
            data_yaml=data_yaml,
            base_model=self.current_model_path,
            output_dir="models/trained/default"
        )

        QMessageBox.information(
            self, 
            "Training Finished",
            "Training complete!\nCheck models/trained/default/v1/best.pt"
        )

    # ------------------------
    def export_dataset(self):
     export_yolo_dataset(
        parent=self,
        dataset_path="storage/datasets/default"
    )
