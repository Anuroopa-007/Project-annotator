import os
from pathlib import Path
from shutil import copy2
import cv2

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QFileDialog, QProgressBar
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage

from ui.canvas.image_view import ImageView
from ui.sidebar import Sidebar
from ui.topbar import TopBar
from PyQt5.QtWidgets import QInputDialog

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
        self.input_mode = None
        self.annotate_mode = "current"
        self.is_paused = False
        self.timer = None

        # Video
        self.video_cap = None
        self.video_timer = None

        # FPS
        self._last_tick = cv2.getTickCount()
        self._fps = 0

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


        self.image_view.scene.clearSelection()
        self.annotation_service.clear()
        self.image_view.load_image(path)
        self.sidebar.set_status("Single image loaded")
        self.refresh_topbar_labels()

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
    # VIDEO PLAYBACK + AUTO ANNOTATION
    # =========================================================
    def _play_video_frame(self):
        if self.is_paused or self.video_cap is None:
            return

        # FPS
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

        service = AutoAnnotateService(self.current_model_path)
        predictions = service.predict(temp_path, conf=0.25)

        # Live counts
        counts = {}
        for cls, *_ in predictions:
            counts[cls] = counts.get(cls, 0) + 1
        self.sidebar.update_detection_counts(counts)
        # ---------------- SAVE VIDEO FRAMES PER CLASS ----------------
        for cls, *_ in predictions:
            class_dir = Path(f"storage/datasets/default/video_detected/{cls}")
            class_dir.mkdir(parents=True, exist_ok=True)

            frame_id = int(self.video_cap.get(cv2.CAP_PROP_POS_FRAMES))
            frame_name = f"{cls}_frame_{frame_id}.jpg"

            cv2.imwrite(str(class_dir / frame_name), frame)


        self.image_view.scene.add_auto_boxes(predictions)
        self.sidebar.set_status(f"FPS: {self._fps}")

    # =========================================================
    # SIDEBAR
    # =========================================================
    def load_image_from_list(self, path):
        self.image_view.scene.clearSelection()
        self.annotation_service.clear()
        self.image_view.load_image(path)
        self.sidebar.highlight_current_image(path)

    # =========================================================
    # TOPBAR CALLBACKS (DO NOT REMOVE)
    # =========================================================
    def on_model_changed(self, text):
        self.current_model_path = f"models/pretrained/{text}"

    def pause_resume(self):
        self.is_paused = not self.is_paused
        self.sidebar.set_status("Paused" if self.is_paused else "Resumed")

    # =========================================================
    # SAVE YOLO
    # =========================================================
    def save_yolo(self):
        scene = self.image_view.scene
        if not scene.image_path:
         return

    # 👉 MANUAL annotations (label, QRectF)
        manual_annotations = self.annotation_service.annotations

        self._save_manual_annotations(manual_annotations, scene.image_path)
        create_data_yaml("storage/datasets/default")
        self.refresh_topbar_labels()
        self.sidebar.set_status("Manual annotations saved")


    # =========================================================
    # AUTO ANNOTATE (REQUIRED BY TOPBAR)
    # =========================================================
    def auto_annotate(self, delay=300):
        service = AutoAnnotateService(self.current_model_path)

    # ---------- SINGLE IMAGE ----------
        if self.input_mode == "single":
            img_path = self.image_paths[self.current_image_index]
            preds = service.predict(img_path, conf=0.25)
            self.image_view.load_image(img_path)
            self.image_view.scene.clear_annotations()
            self.image_view.scene.add_auto_boxes(preds)
            self._annotate_frame(preds, img_path)
            self.sidebar.set_status("Image auto-annotated")
            return

    # ---------- FOLDER (ONLY CURRENT IMAGE) ----------
        if self.input_mode == "folder":
            img_path = self.image_paths[self.current_image_index]
            preds = service.predict(img_path, conf=0.25)
            self.image_view.load_image(img_path)
            self.image_view.scene.clear_annotations()
            self.image_view.scene.add_auto_boxes(preds)
            self._annotate_frame(preds, img_path)
            self.sidebar.set_status("Current image auto-annotated")
            return

    # ---------- VIDEO (CONTINUOUS – already handled in _play_video_frame) ----------
        if self.input_mode == "video":
            self.sidebar.set_status("Video auto-annotation running")
            return

    # def auto_annotate(self, delay=300):
    #     service = AutoAnnotateService(self.current_model_path)

    #     if self.input_mode not in ["single", "folder"]:
    #         return

    #     self.progress_bar.setVisible(True)
    #     self.progress_bar.setMaximum(len(self.image_paths))
    #     self.progress_bar.setValue(0)

    #     self.timer = QTimer()

    #     def process_next():
    #         if self.current_image_index >= len(self.image_paths):
    #             self.timer.stop()
    #             self.progress_bar.setVisible(False)
    #             create_data_yaml("storage/datasets/default")
    #             self.sidebar.set_status("Auto-annotation completed")
    #             return

    #         img_path = self.image_paths[self.current_image_index]
    #         preds = service.predict(img_path, conf=0.25)
    #         self._annotate_frame(preds, img_path)

    #         self.progress_bar.setValue(self.current_image_index + 1)
    #         self.current_image_index += 1

    #     self.timer.timeout.connect(process_next)
    #     self.timer.start(delay)

    # =========================================================
    # CORE YOLO SAVE
    # =========================================================
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
                 continue 
                # classes.append(cls)
            cid = classes.index(cls)

            xc = x_center
            yc =  y_center
            bw = w_norm
            bh = h_norm

            if bw > 0 and bh > 0:
                lines.append(f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

        (labels_dir / f"{Path(img_path).stem}.txt").write_text("\n".join(lines))
        copy2(img_path, images_dir / Path(img_path).name)
        # ---------------- SAVE IMAGES PER CLASS ----------------
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
                classes.append(label)

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

    # Save label file
        (labels_dir / f"{Path(img_path).stem}.txt").write_text("\n".join(lines))

    # Copy image
        copy2(img_path, images_dir / Path(img_path).name)

    # Save updated classes
        save_classes(dataset_root, classes)


    # def _save_manual_annotations(self, annotations, img_path):
    #     labels_dir = Path("storage/datasets/default/labels/train")
    #     images_dir = Path("storage/datasets/default/images/train")
    #     labels_dir.mkdir(parents=True, exist_ok=True)
    #     images_dir.mkdir(parents=True, exist_ok=True)

    #     classes_file = Path("storage/datasets/default/classes.txt")
    #     classes = classes_file.read_text().splitlines() if classes_file.exists() else []

    #     img = cv2.imread(img_path)
    #     img_h, img_w = img.shape[:2]

    #     lines = []

    #     for label, rect in annotations:
    #         if label not in classes:
    #             classes.append(label)
    #         cid = classes.index(label)

    #         x = rect.x()
    #         y = rect.y()
    #         w = rect.width()
    #         h = rect.height()

    #         xc = (x + w / 2) / img_w
    #         yc = (y + h / 2) / img_h
    #         bw = w / img_w
    #         bh = h / img_h

    #         if bw > 0 and bh > 0:
    #             lines.append(f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

    #     (labels_dir / f"{Path(img_path).stem}.txt").write_text("\n".join(lines))
    #     copy2(img_path, images_dir / Path(img_path).name)
    #     save_classes("storage/datasets/default", classes)


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
            if rect == item.rect():
                updated.append((new_label, rect))
            else:
                updated.append((lbl, rect))

        self.annotation_service.annotations = updated
        self.sidebar.set_status(f"{old_label} → {new_label}")

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

        new_label, ok = QInputDialog.getText(
            self,
            "Edit Label",
            "Enter new label:",
            text=item.label 
        )

        if not ok or not new_label.strip():
            return

        old_label = item.label
        item.label = new_label
        item.text_item.setPlainText(new_label)

    # Update annotation service
        updated = []
        for lbl, rect in self.annotation_service.annotations:
            if rect == item.rect():
                updated.append((new_label, rect))
            else:
                updated.append((lbl, rect))

        self.annotation_service.annotations = updated
        self.sidebar.set_status(f"{old_label} → {new_label}")
        self.refresh_topbar_labels()
        # 🔹 Deselect after edit
        # item.setSelected(False)
        # self.image_view.scene.clearSelection()




    def delete_selected_box(self):
        scene = self.image_view.scene
        selected = scene.selectedItems()

        if not selected:
            QMessageBox.information(self, "No Selection", "Select a box first")
            return

        item = selected[0]
        scene.removeItem(item)

    # Remove from annotation service
        self.annotation_service.annotations = [
            (lbl, rect)
            for lbl, rect in self.annotation_service.annotations
            if rect != item.rect()
        ]

        self.sidebar.set_status("Box deleted")

    def on_action_selected(self, text):
        if text == "Edit Label":
            self.parent.edit_selected_box()

        elif text == "Delete Box":
            self.parent.delete_selected_box()

        elif text.startswith("Reuse:"):
            label = text.replace("Reuse:", "").strip()
            self.parent.apply_label_to_selected_box(label)

        self.action_combo.setCurrentIndex(0)

