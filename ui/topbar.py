# topbar.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox
)
from PyQt5.QtCore import Qt


class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.setFixedHeight(60)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; border-bottom: 1px solid #333; }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover { background-color: #005a9e; }
            QLabel { color: white; font-size: 14px; padding: 0 20px; }
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #444;
                padding: 8px;
                border-radius: 4px;
        }
            QComboBox QAbstractItemView {
                    background-color: #1e1e1e;
                    color: white;
                    selection-background-color: #007acc;
                    selection-color: white;
        }

        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        # ---------------- LEFT ----------------
        self.open_image_btn = QPushButton("📄 Open Image")
        self.open_image_btn.clicked.connect(parent.load_image)

        self.open_folder_btn = QPushButton("📁 Open Folder")
        self.open_folder_btn.clicked.connect(parent.load_folder)

        self.open_video_btn = QPushButton("🎥 Open Video")
        self.open_video_btn.clicked.connect(parent.load_video)

        layout.addWidget(self.open_image_btn)
        layout.addWidget(self.open_folder_btn)
        layout.addWidget(self.open_video_btn)

        layout.addStretch()

        # ---------------- MODEL SELECT ----------------
        self.model_combo = QComboBox()
        self.model_combo.addItems(["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"])
        self.model_combo.currentTextChanged.connect(parent.on_model_changed)
        layout.addWidget(self.model_combo)

        layout.addStretch()

        # ---------------- ANNOTATION ACTIONS DROPDOWN ----------------
        self.action_combo = QComboBox()
        self.action_combo.addItem("Annotation Actions")
        self.action_combo.addItem("Change Label")
        self.action_combo.addItem("Delete Box")
        self.action_combo.currentIndexChanged.connect(self.on_action_selected)

        layout.addWidget(self.action_combo)

        # ---------------- RIGHT BUTTONS ----------------
        self.auto_btn = QPushButton("🤖 Auto Annotate")
        self.auto_btn.clicked.connect(parent.auto_annotate)

        self.save_btn = QPushButton("💾 Save YOLO")
        self.save_btn.clicked.connect(parent.save_yolo)

        self.train_btn = QPushButton("🚀 Train YOLO")
        self.train_btn.clicked.connect(parent.train_model)

        self.export_btn = QPushButton("📦 Export YOLO")
        self.export_btn.clicked.connect(parent.export_dataset)

        self.pause_btn = QPushButton("⏸ Pause/Resume")
        self.pause_btn.clicked.connect(parent.pause_resume)

        layout.addWidget(self.auto_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.train_btn)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.pause_btn)

    # =====================================================
    # DROPDOWN HANDLER
    # =====================================================
    def on_action_selected(self, index):
        text = self.action_combo.currentText()

        # reset dropdown immediately
        self.action_combo.setCurrentIndex(0)

        if text == "Change Label":
            self.parent.edit_selected_box()

        elif text == "Delete Box":
            self.parent.delete_selected_box()

        elif text.startswith("Reuse:"):
            label = text.replace("Reuse:", "").strip()
            self.parent.apply_label_to_selected_box(label)

    # =====================================================
    # UPDATE REUSABLE LABELS (CALL FROM MAIN WINDOW)
    # =====================================================
    def refresh_label_actions(self, labels):
        self.action_combo.blockSignals(True)
        self.action_combo.clear()

        self.action_combo.addItem("Annotation Actions")
        self.action_combo.addItem("Change Label")
        self.action_combo.addItem("Delete Box")

        for lbl in labels:
            self.action_combo.addItem(f"Reuse: {lbl}")

        self.action_combo.blockSignals(False)
