from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from ui.canvas.image_view import ImageView
from services.annotation_service import AnnotationService
from formats.yolo import YOLOExporter
from services.auto_annotate_service import AutoAnnotateService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CV Annotator")
        self.resize(1200, 800)

        # Annotation service
        self.annotation_service = AnnotationService()

        # Image view (canvas)
        self.image_view = ImageView(self.annotation_service)

        # Buttons
        load_btn = QPushButton("Load Image")
        save_btn = QPushButton("Save YOLO")
        auto_btn = QPushButton("Auto Annotate")

        # Connect buttons
        load_btn.clicked.connect(self.load_image)
        save_btn.clicked.connect(self.save_yolo)
        auto_btn.clicked.connect(self.auto_annotate)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(load_btn)
        layout.addWidget(auto_btn)
        layout.addWidget(save_btn)
        layout.addWidget(self.image_view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # -----------------------------
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.jpg *.png *.jpeg)"
        )
        if path:
            self.image_view.load_image(path)

    # -----------------------------
    def save_yolo(self):
        if not self.image_view.image_path or not self.annotation_service.annotations:
            QMessageBox.warning(self, "Error", "No image or annotations to save")
            return

        YOLOExporter.export(
            image_path=self.image_view.image_path,
            annotations=self.annotation_service.annotations
        )

        QMessageBox.information(
            self,
            "Saved Successfully ✅",
            f"YOLO labels saved for:\n{self.image_view.image_path}"
        )

    # -----------------------------
    def auto_annotate(self):
        if not self.image_view.image_path:
            QMessageBox.warning(self, "Error", "Load an image first")
            return

        model_path = "models/pretrained/yolov8n.pt"
        service = AutoAnnotateService(model_path)

        # Run prediction
        predictions = service.predict(
            self.image_view.image_path,
            conf=0.25
        )

        # Add boxes to the scene (this should create BBoxItems in your canvas)
        self.image_view.scene.add_auto_boxes(predictions)

        QMessageBox.information(
            self,
            "Auto Annotation Complete",
            f"Detected {len(predictions)} objects"
        )
