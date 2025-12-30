# ui/topbar.py - FINAL FIXED & CVAT PROFESSIONAL STYLE
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QToolButton, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.themes import THEMES

class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # File Menu
        file_menu = QMenu()
        file_menu.addAction("📄 Open Image", parent.load_image)
        file_menu.addAction("📁 Open Folder", parent.load_folder)
        file_menu.addAction("🎥 Open Video", parent.load_video)
        file_btn = QToolButton()
        file_btn.setText("File")
        file_btn.setMenu(file_menu)
        file_btn.setPopupMode(QToolButton.InstantPopup)
        file_btn.setStyleSheet("font-weight: bold;")
        layout.addWidget(file_btn)

        # View Menu
        view_menu = QMenu()
        view_menu.addAction("➕ Zoom In", lambda: parent.image_view.scale(1.25, 1.25))
        view_menu.addAction("➖ Zoom Out", lambda: parent.image_view.scale(0.8, 0.8))
        view_menu.addAction("🔄 Reset View", lambda: parent.image_view.resetTransform())
        view_menu.addSeparator()
        view_menu.addAction("↶ Undo", parent.undo_action)
        view_menu.addAction("↷ Redo", parent.redo_action)
        view_btn = QToolButton()
        view_btn.setText("View")
        view_btn.setMenu(view_menu)
        view_btn.setPopupMode(QToolButton.InstantPopup)
        view_btn.setStyleSheet("font-weight: bold;")
        layout.addWidget(view_btn)

        layout.addStretch()

        # Model
        layout.addWidget(QLabel("Model:"))
        model_combo = QComboBox()
        model_combo.addItems(["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"])
        model_combo.currentTextChanged.connect(parent.on_model_changed)
        layout.addWidget(model_combo)

        layout.addStretch()

        # Actions dropdown
        actions_label = QLabel("Actions:")
        self.action_combo = QComboBox()  # ← Save as instance variable
        self.action_combo.addItem("Annotation Actions")
        self.action_combo.addItem("Change Label")
        self.action_combo.addItem("Delete Box")
        # ✅ FIXED: Connect to self.on_action_selected (not parent.topbar)
        self.action_combo.currentIndexChanged.connect(self.on_action_selected)
        layout.addWidget(actions_label)
        layout.addWidget(self.action_combo)

        layout.addStretch()
        # Add this button after "Actions:" section
        polygon_btn = QPushButton("Polygon Mode")
        polygon_btn.setCheckable(True)
        polygon_btn.setChecked(False)
        polygon_btn.toggled.connect(parent.toggle_polygon_mode)
        layout.addWidget(polygon_btn)

        # Main buttons — CREATE FIRST, THEN CONNECT
        auto_btn = QPushButton("🤖 Auto Annotate")
        auto_btn.clicked.connect(parent.auto_annotate)
        layout.addWidget(auto_btn)

        save_btn = QPushButton("💾 Save YOLO")
        save_btn.clicked.connect(parent.save_yolo)
        layout.addWidget(save_btn)

        train_btn = QPushButton("🚀 Train")
        train_btn.clicked.connect(parent.train_model)
        layout.addWidget(train_btn)

        export_btn = QPushButton("📦 Export")
        export_btn.clicked.connect(parent.export_dataset)
        layout.addWidget(export_btn)

        pause_btn = QPushButton("⏸ Pause/Resume")
        pause_btn.clicked.connect(parent.pause_resume)
        layout.addWidget(pause_btn)

        layout.addStretch()

        # Theme switcher
        layout.addWidget(QLabel("Theme:"))
        theme_combo = QComboBox()
        theme_combo.addItems([v["name"] for v in THEMES.values()])
        theme_combo.setCurrentText("CVAT Dark")
        theme_combo.currentTextChanged.connect(parent.apply_global_theme_by_name)
        layout.addWidget(theme_combo)

        # Apply initial theme
        self.apply_theme("cvat_dark")

    def apply_theme(self, theme_name):
        t = THEMES[theme_name]
        self.setStyleSheet(f"""
            QWidget {{ background: {t['bg']}; border-bottom: 1px solid {t['border']}; }}
            QLabel {{ color: {t['text_secondary']}; font-size: 13px; }}
            QToolButton {{ background: transparent; color: {t['text']}; font-weight: bold; padding: 8px; }}
            QToolButton:hover {{ background: {t['surface2']}; border-radius: 4px; }}
            QPushButton {{ background: {t['accent']}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: 600; }}
            QPushButton:hover {{ background: {t['accent_hover']}; }}
            QComboBox {{ background: {t['surface']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 6px; }}
        """)

    def on_action_selected(self, index):
        text = self.action_combo.currentText()
        self.action_combo.setCurrentIndex(0)  # Reset dropdown

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