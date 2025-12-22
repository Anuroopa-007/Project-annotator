import os
from pathlib import Path
from shutil import copy2
from PIL import Image

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QFileDialog, QProgressBar
)
from PyQt5.QtCore import QTimer

from ui.canvas.image_view import ImageView
from ui.sidebar import Sidebar
from ui.topbar import TopBar

from services.annotation_service import AnnotationService
from services.auto_annotate_service import AutoAnnotateService
from services.dataset_service import create_data_yaml, save_classes
from services.training_service import train_yolo
from services.export_service import export_yolo_dataset


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CV Annotator")
        self.resize(1600, 900)

        # ---------------- STATE ----------------
        self.current_model_path = "models/pretrained/yolov8n.pt"
        self.image_paths = []
        self.current_image_index = 0
        self.input_mode = None           # single | folder | video
        self.annotate_mode = "current"   # current | all
        self.is_paused = False
        self.timer = None

        # ---------------- SERVICES ----------------
        self.annotation_service = AnnotationService()
        self.image_view = ImageView(self.annotation_service)

        # ---------------- UI ----------------
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        self.topbar = TopBar(self)
        main_layout.addWidget(self.topbar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        content_layout = QHBoxLayout()
        self.sidebar = Sidebar(self)

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.image_view, stretch=1)

        main_layout.addLayout(content_layout)
        self.setCentralWidget(central_widget)

    # =========================================================
    # LOADERS
    # =========================================================
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.jpg *.png *.jpeg *.bmp)"
        )
        if not path:
            return

        self.input_mode = "single"
        self.image_paths = [path]
        self.current_image_index = 0

        self.annotation_service.clear()
        self.image_view.load_image(path)
        self.sidebar.set_status("Single image loaded")

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return

        self.input_mode = "folder"
        self.image_paths = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
        )

        if not self.image_paths:
            QMessageBox.warning(self, "Empty", "No images found")
            return

        self.current_image_index = 0
        self.sidebar.populate_images(self.image_paths)
        self.load_image_from_list(self.image_paths[0])

        self.sidebar.set_status(f"{len(self.image_paths)} images loaded")

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Videos (*.mp4 *.avi *.mov *.mkv)"
        )
        if not path:
            return

        from services.video_service import extract_frames

        self.input_mode = "video"
        self.image_paths = extract_frames(path, "storage/temp/video_frames", every_n=5)

        if not self.image_paths:
            QMessageBox.warning(self, "Error", "No frames extracted")
            return

        self.current_image_index = 0
        self.sidebar.populate_images(self.image_paths)
        self.sidebar.set_status(f"{len(self.image_paths)} frames extracted")

    # =========================================================
    # SIDEBAR CALLBACK (REQUIRED)
    # =========================================================
    def load_image_from_list(self, path):
        if path not in self.image_paths:
            return

        self.current_image_index = self.image_paths.index(path)
        self.annotation_service.clear()
        self.image_view.load_image(path)

        self.sidebar.highlight_current_image(path)
        self.sidebar.set_status(f"Loaded: {os.path.basename(path)}")

    # =========================================================
    # TOPBAR CALLBACKS (REQUIRED)
    # =========================================================
    def on_model_changed(self, text):
        self.current_model_path = f"models/pretrained/{text}"

    def toggle_annotate_mode(self):
        self.annotate_mode = "all" if self.annotate_mode == "current" else "current"
        self.sidebar.set_status(f"Annotate mode: {self.annotate_mode.upper()}")

    def pause_resume(self):
        self.is_paused = not self.is_paused
        self.sidebar.set_status("Paused" if self.is_paused else "Resumed")

    # =========================================================
    # SAVE YOLO (REQUIRED BY TOPBAR)
    # =========================================================
    def save_yolo(self):
        if not hasattr(self.image_view, "image_path"):
            QMessageBox.warning(self, "Error", "No image loaded")
            return

        if not self.annotation_service.annotations:
            QMessageBox.warning(self, "Error", "No annotations to save")
            return

        from formats.yolo import YOLOExporter
        split = "train" if self.annotate_mode == "current" else "val"

        YOLOExporter.export(
            image_path=self.image_view.image_path,
            annotations=self.annotation_service.annotations,
            dataset_path="storage/datasets/default",
            split=split
        )


        # YOLOExporter.export(
        #     image_path=self.image_view.image_path,
        #     annotations=self.annotation_service.annotations,
        #     dataset_path="storage/datasets/default",
        #     split="train"
        # )

        create_data_yaml("storage/datasets/default")
        self.sidebar.set_status("YOLO saved")

    # =========================================================
    # AUTO ANNOTATION
    # =========================================================
    def auto_annotate(self, delay=300):
        if not self.image_paths:
            QMessageBox.warning(self, "Error", "Load data first")
            return

        service = AutoAnnotateService(self.current_model_path)

        # ---- CURRENT IMAGE ONLY ----
        if self.annotate_mode == "current":
            img_path = self.image_paths[self.current_image_index]
            self._annotate_single(service, img_path)
            self.sidebar.set_status("Current image annotated")
            return

        # ---- ALL (FOLDER / VIDEO SLIDESHOW) ----
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)

        self.is_paused = False
        self.timer = QTimer()

        def process_next():
            if self.is_paused:
                return

            if self.current_image_index >= len(self.image_paths):
                self.timer.stop()
                self.progress_bar.setVisible(False)
                create_data_yaml("storage/datasets/default")
                self.sidebar.set_status("Auto-annotation completed")
                return

            img_path = self.image_paths[self.current_image_index]
            self._annotate_single(service, img_path)

            self.progress_bar.setValue(self.current_image_index + 1)
            self.sidebar.set_status(
                f"Annotating {self.current_image_index + 1}/{len(self.image_paths)}"
            )

            self.current_image_index += 1

        self.timer.timeout.connect(process_next)
        self.timer.start(delay)

    # =========================================================
    # CORE YOLO LOGIC
    # =========================================================
    def _annotate_single(self, service, img_path):
        predictions = service.predict(img_path, conf=0.25)

        self.image_view.load_image(img_path)
        self.image_view.scene.clear_annotations()
        self.image_view.scene.add_auto_boxes(predictions)
        # Decide split based on annotate mode
        split = "train" if self.annotate_mode == "current" else "val"

        labels_dir = Path(f"storage/datasets/default/labels/{split}")
        images_dir = Path(f"storage/datasets/default/images/{split}")
        labels_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)


        # labels_dir = Path("storage/datasets/default/labels/train")
        # images_dir = Path("storage/datasets/default/images/train")
        # labels_dir.mkdir(parents=True, exist_ok=True)
        # images_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load existing classes.txt ----
        classes_file = Path("storage/datasets/default/classes.txt")
        if classes_file.exists():
            classes = classes_file.read_text().splitlines()
        else:
            classes = []

        lines = []

        for cls, x, y, w, h, *_ in predictions:
        # cls is STRING like "person"
            if cls not in classes:
                classes.append(cls)

            cid = classes.index(cls)

            lines.append(
                f"{cid} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
        )

    # ---- Save label file ----
        (labels_dir / f"{Path(img_path).stem}.txt").write_text("\n".join(lines))

    # ---- Copy image ----
        copy2(img_path, images_dir / Path(img_path).name)

    # ---- Save updated classes ----
        save_classes("storage/datasets/default", classes)


    # =========================================================
    # TRAIN / EXPORT
    # =========================================================
    def train_model(self):
        train_yolo(
            "storage/datasets/default/data.yaml",
            self.current_model_path,
            "models/trained/default"
        )

    def export_dataset(self):
        export_yolo_dataset(self, "storage/datasets/default")
