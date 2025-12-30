import os
from pathlib import Path
from shutil import copy2
import cv2

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QFileDialog, QProgressBar, QInputDialog
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage

from ui.canvas.image_view import ImageView
from ui.sidebar import Sidebar
from ui.topbar import TopBar
from ui.right_panel import RightPanel

from services.annotation_service import AnnotationService
from services.auto_annotate_service import AutoAnnotateService
from services.dataset_service import create_data_yaml, save_classes
from services.training_service import train_yolo
from services.export_service import export_yolo_dataset

from ui.themes import THEMES, get_stylesheet
from ultralytics import YOLO  # ← For tracking


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CV Annotator")
        self.resize(1600, 900)

        # ---------------- STATE ----------------
        self.current_model_path = "models/pretrained/yolov8n.pt"
        self.image_paths = []
        self.current_image_index = 0
        self.input_mode = None
        self.annotate_mode = "current"
        self.is_paused = False
        self.timer = None
        self.video_cap = None
        self.video_timer = None
        self._last_tick = cv2.getTickCount()
        self._fps = 0

        # ---------------- SERVICES ----------------
        self.annotation_service = AnnotationService()
        self.image_view = ImageView(self.annotation_service)

        # ---------------- YOLO MODEL (Loaded once for speed & tracking) ----------------
        self.model = YOLO(self.current_model_path)  # ← LOAD MODEL ONCE

        # ---------------- UI ----------------
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.topbar = TopBar(self)
        main_layout.addWidget(self.topbar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4)
        main_layout.addWidget(self.progress_bar)

        content_layout = QHBoxLayout()
        self.sidebar = Sidebar(self)
        content_layout.addWidget(self.sidebar)

        self.right_panel = RightPanel(self)
        content_layout.addWidget(self.right_panel)

        content_layout.addWidget(self.image_view, stretch=1)
        main_layout.addLayout(content_layout)
        self.setCentralWidget(central_widget)

        # ---------------- THEME ----------------
        self.current_theme = "cvat_dark"
        self.apply_global_theme(self.current_theme)

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

        self.image_view.scene.clearSelection()
        self.annotation_service.clear()
        self.image_view.load_image(path)
        self.sidebar.set_status("Single image loaded")
        self.refresh_topbar_labels()
        self.refresh_objects()

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

        self.sidebar.populate_images(self.image_paths)
        self.load_image_from_list(self.image_paths[0])
        self.refresh_topbar_labels()

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Videos (*.mp4 *.avi *.mov *.mkv)"
        )
        if not path:
            return

        self.input_mode = "video"
        self.video_cap = cv2.VideoCapture(path)

        if not self.video_cap.isOpened():
            QMessageBox.warning(self, "Error", "Cannot open video")
            return

        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self._play_video_frame)
        self.video_timer.start(30)

        self.sidebar.set_status("Video playing...")

    # =========================================================
    # VIDEO PLAYBACK + OBJECT TRACKING
    # =========================================================
    def _play_video_frame(self):
        if self.is_paused or self.video_cap is None:
            return

        current_tick = cv2.getTickCount()
        diff = (current_tick - self._last_tick) / cv2.getTickFrequency()
        self._fps = int(1 / diff) if diff > 0 else 0
        self._last_tick = current_tick

        ret, frame = self.video_cap.read()
        if not ret:
            self.video_timer.stop()
            self.video_cap.release()
            self.sidebar.set_status("Video ended")
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        qimage = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)

        self.image_view.scene.set_video_frame(qimage)
        self.image_view.scene.clear_annotations()

        temp_path = "storage/temp/video_frame.jpg"
        os.makedirs("storage/temp", exist_ok=True)
        cv2.imwrite(temp_path, frame)

        # ✅ OBJECT TRACKING USING YOLOv8 TRACKER
        results = self.model.track(temp_path, conf=0.25, persist=True, tracker="bytetrack.yaml")[0]

        predictions = []
        track_ids = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id].lower()
            x, y, w, h = box.xywhn[0].tolist()  # normalized
            predictions.append((label, x, y, w, h))
            track_id = int(box.id.item()) if box.id is not None else None
            track_ids.append(track_id)

        # Live counts
        counts = {}
        for cls, *_ in predictions:
            counts[cls] = counts.get(cls, 0) + 1
        self.sidebar.update_detection_counts(counts)

        # Save frames per class
        for cls, *_ in predictions:
            class_dir = Path(f"storage/datasets/default/video_detected/{cls}")
            class_dir.mkdir(parents=True, exist_ok=True)
            frame_id = int(self.video_cap.get(cv2.CAP_PROP_POS_FRAMES))
            frame_name = f"{cls}_frame_{frame_id}.jpg"
            cv2.imwrite(str(class_dir / frame_name), frame)

        # Display with track IDs
        self.image_view.scene.add_auto_boxes(predictions, track_ids)
        self.sidebar.set_status(f"FPS: {self._fps} | Tracking Active")

    # =========================================================
    # SIDEBAR
    # =========================================================
    def load_image_from_list(self, path):
        if path in self.image_paths:
            self.current_image_index = self.image_paths.index(path)

        self.image_view.scene.clearSelection()
        self.annotation_service.clear()
        self.image_view.load_image(path)
        self.sidebar.highlight_current_image(path)
        self.refresh_objects()

    # =========================================================
    # TOPBAR CALLBACKS
    # =========================================================
    def on_model_changed(self, text):
        self.current_model_path = f"models/pretrained/{text}"
        self.model = YOLO(self.current_model_path)  # Reload model
        self.sidebar.set_status(f"Model changed: {text}")

    def pause_resume(self):
        self.is_paused = not self.is_paused
        self.sidebar.set_status("Paused" if self.is_paused else "Resumed")

    def toggle_polygon_mode(self, checked):
        self.image_view.scene.set_polygon_mode(checked)
        self.sidebar.set_status("Polygon Mode" if checked else "Rectangle Mode")

    # =========================================================
    # SAVE / ANNOTATE
    # =========================================================
    def save_yolo(self):
        scene = self.image_view.scene
        if not scene.image_path:
            return

        manual_annotations = self.annotation_service.annotations
        self._save_manual_annotations(manual_annotations, scene.image_path)
        create_data_yaml("storage/datasets/default")
        self.refresh_topbar_labels()
        self.sidebar.set_status("Manual annotations saved")
        self.refresh_objects()

    def auto_annotate(self):
        service = AutoAnnotateService(self.current_model_path)

        if self.input_mode == "single" or self.input_mode == "folder":
            img_path = self.image_paths[self.current_image_index]
            preds = service.predict(img_path, conf=0.25)

            scene = self.image_view.scene
            scene.clear_annotations()
            scene.add_auto_boxes(preds)

            self._annotate_frame(preds, img_path)
            self.sidebar.set_status("Auto-annotated current image")
            self.refresh_objects()

        elif self.input_mode == "video":
            self.sidebar.set_status("Video auto-tracking running")

    def _annotate_frame(self, predictions, img_path):
        split = "train"
        labels_dir = Path(f"storage/datasets/default/labels/{split}")
        images_dir = Path(f"storage/datasets/default/images/{split}")
        labels_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        classes_file = Path("storage/datasets/default/classes.txt")
        classes = classes_file.read_text().splitlines() if classes_file.exists() else []

        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        lines = []

        for cls, x_center, y_center, w_norm, h_norm in predictions:
            if cls not in classes:
                print(f"[WARN] Unknown class skipped: {cls}")
                continue
            cid = classes.index(cls)
            if w_norm > 0 and h_norm > 0:
                lines.append(f"{cid} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

        (labels_dir / f"{Path(img_path).stem}.txt").write_text("\n".join(lines))
        copy2(img_path, images_dir / Path(img_path).name)

        for cls, *_ in predictions:
            class_img_dir = Path(f"storage/datasets/default/images_by_class/{cls}")
            class_img_dir.mkdir(parents=True, exist_ok=True)
            copy2(img_path, class_img_dir / Path(img_path).name)

        save_classes("storage/datasets/default", classes)

    def _save_manual_annotations(self, annotations, img_path):
        dataset_root = Path("storage/datasets/default")
        labels_dir = dataset_root / "labels" / "train"
        images_dir = dataset_root / "images" / "train"
        labels_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        classes_file = dataset_root / "classes.txt"
        classes = classes_file.read_text().splitlines() if classes_file.exists() else []

        img = cv2.imread(img_path)
        img_h, img_w = img.shape[:2]
        lines = []

        for label, rect in annotations:
            label = label.strip().lower()
            if label not in classes:
                QMessageBox.warning(self, "Invalid Label", f"Label '{label}' not found in classes.txt")
                continue
            cls_id = classes.index(label)

            x = rect.x()
            y = rect.y()
            w = rect.width()
            h = rect.height()

            xc = (x + w / 2) / img_w
            yc = (y + h / 2) / img_h
            bw = w / img_w
            bh = h / img_h

            if bw > 0 and bh > 0:
                lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

        (labels_dir / f"{Path(img_path).stem}.txt").write_text("\n".join(lines))
        copy2(img_path, images_dir / Path(img_path).name)
        save_classes(dataset_root, classes)

    # =========================================================
    # OTHER
    # =========================================================
    def train_model(self):
        train_yolo("storage/datasets/default/data.yaml", self.current_model_path, "models/trained/default")

    def export_dataset(self):
        export_yolo_dataset(self, "storage/datasets/default")

    def apply_label_to_selected_box(self, new_label):
        scene = self.image_view.scene
        selected = scene.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select a box first")
            return
        item = selected[0]
        old_label = item.label
        item.label = new_label
        item.text_item.setPlainText(new_label)

        updated = []
        for lbl, rect in self.annotation_service.annotations:
            updated.append((new_label, rect) if rect == item.rect() else (lbl, rect))
        self.annotation_service.annotations = updated
        self.sidebar.set_status(f"{old_label} → {new_label}")
        self.refresh_objects()

    def refresh_topbar_labels(self):
        classes_file = Path("storage/datasets/default/classes.txt")
        if classes_file.exists():
            labels = classes_file.read_text().splitlines()
            self.topbar.refresh_label_actions(labels)

    def edit_selected_box(self):
        scene = self.image_view.scene
        selected = scene.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select a box first")
            return
        item = selected[0]
        new_label, ok = QInputDialog.getText(self, "Edit Label", "Enter new label:", text=item.label)
        if not ok or not new_label.strip():
            return
        old_label = item.label
        item.label = new_label
        item.text_item.setPlainText(new_label)

        updated = []
        for lbl, rect in self.annotation_service.annotations:
            updated.append((new_label, rect) if rect == item.rect() else (lbl, rect))
        self.annotation_service.annotations = updated
        self.sidebar.set_status(f"{old_label} → {new_label}")
        self.refresh_topbar_labels()
        self.refresh_objects()

    def delete_selected_box(self):
        scene = self.image_view.scene
        selected = scene.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select a box first")
            return
        item = selected[0]
        scene.removeItem(item)
        self.annotation_service.annotations = [
            (lbl, rect) for lbl, rect in self.annotation_service.annotations if rect != item.rect()
        ]
        self.sidebar.set_status("Box deleted")
        self.refresh_objects()

    def apply_global_theme(self, theme_name: str):
        self.current_theme = theme_name
        stylesheet = get_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)
        self.sidebar.apply_theme(theme_name)
        self.topbar.apply_theme(theme_name)
        self.sidebar.set_status(f"Theme: {THEMES[theme_name]['name']} applied ✨")

    def apply_global_theme_by_name(self, name):
        key = next(k for k, v in THEMES.items() if v["name"] == name)
        self.apply_global_theme(key)

    def undo_action(self):
        self.annotation_service.undo()
        self.image_view.scene.clear()
        self.image_view.load_image(self.image_view.image_path)
        for label, rect in self.annotation_service.annotations:
            self.image_view.scene.addItem(BBoxItem(rect, label))
        self.refresh_objects()

    def redo_action(self):
        self.annotation_service.redo()
        self.image_view.scene.clear()
        self.image_view.load_image(self.image_view.image_path)
        for label, rect in self.annotation_service.annotations:
            self.image_view.scene.addItem(BBoxItem(rect, label))
        self.refresh_objects()

    def refresh_objects(self):
        if hasattr(self, 'right_panel'):
            self.right_panel.update_objects(self.annotation_service.annotations)

    def toggle_polygon_mode(self, checked):
        self.image_view.set_polygon_mode(checked)
        self.sidebar.set_status("Smart Polygon Mode" if checked else "Rectangle Mode")