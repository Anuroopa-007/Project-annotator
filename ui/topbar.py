# ui/topbar.py - COMPLETE REPLACEMENT (Theme Support + All Buttons)
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
from ui.themes import THEMES, get_stylesheet  # Correct path

class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(64)
        self.current_theme = "dark"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        # ---------------- LEFT: OPEN BUTTONS ----------------
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
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"])
        self.model_combo.currentTextChanged.connect(parent.on_model_changed)
        layout.addWidget(model_label)
        layout.addWidget(self.model_combo)

        layout.addStretch()

        # ---------------- ANNOTATION ACTIONS ----------------
        action_label = QLabel("Actions:")
        self.action_combo = QComboBox()
        self.action_combo.addItem("Annotation Actions")
        self.action_combo.addItem("Change Label")
        self.action_combo.addItem("Delete Box")
        self.action_combo.currentIndexChanged.connect(self.on_action_selected)
        layout.addWidget(action_label)
        layout.addWidget(self.action_combo)

        layout.addStretch()

        # ---------------- RIGHT: MAIN BUTTONS ----------------
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

        layout.addStretch()

        # ---------------- THEME SWITCHER (TOP RIGHT) ----------------
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([t["name"] for t in THEMES.values()])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combo)

        self.apply_theme(self.current_theme)

    def apply_theme(self, theme_name: str):
        self.current_theme = theme_name
        self.setStyleSheet(f"""
            QWidget {{ 
                background-color: {THEMES[theme_name]['bg']}; 
                border-bottom: 1px solid {THEMES[theme_name]['border']}; 
            }}
            QLabel {{ color: {THEMES[theme_name]['text']}; font-size: 13px; }}
            QPushButton {{ 
                background-color: {THEMES[theme_name]['accent']};
                color: white; border: none; padding: 8px 16px; 
                border-radius: 6px; font-size: 14px; font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {THEMES[theme_name]['accent_hover']}; }}
            QComboBox {{ 
                background-color: {THEMES[theme_name]['surface']};
                color: {THEMES[theme_name]['text']}; 
                border: 1px solid {THEMES[theme_name]['border']}; 
                padding: 8px 12px; border-radius: 6px; min-width: 120px;
            }}
            QComboBox QAbstractItemView {{ 
                background-color: {THEMES[theme_name]['surface']};
                selection-background-color: {THEMES[theme_name]['accent']};
            }}
        """)

    def on_theme_changed(self, theme_name):
        """Find theme key from display name and apply globally"""
        theme_key = next(k for k, v in THEMES.items() if v["name"] == theme_name)
        self.parent.apply_global_theme(theme_key)

    def on_action_selected(self, index):
        text = self.action_combo.currentText()
        self.action_combo.setCurrentIndex(0)  # Reset

        if text == "Change Label":
            self.parent.edit_selected_box()
        elif text == "Delete Box":
            self.parent.delete_selected_box()

    def refresh_label_actions(self, labels):
        self.action_combo.blockSignals(True)
        self.action_combo.clear()
        self.action_combo.addItem("Annotation Actions")
        self.action_combo.addItem("Change Label")
        self.action_combo.addItem("Delete Box")
        for lbl in labels:
            self.action_combo.addItem(f"Reuse: {lbl}")
        self.action_combo.blockSignals(False)