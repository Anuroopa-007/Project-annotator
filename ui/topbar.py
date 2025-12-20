# topbar.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox
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
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        # Left side
        self.open_image_btn = QPushButton("📄 Open Image")
        self.open_image_btn.clicked.connect(parent.load_image)

        self.open_folder_btn = QPushButton("📁 Open Folder")
        self.open_folder_btn.clicked.connect(parent.load_folder)

        layout.addWidget(self.open_image_btn)
        layout.addWidget(self.open_folder_btn)

        layout.addStretch()

        # Center - Model selector
        self.model_combo = QComboBox()
        self.model_combo.addItems(["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"])
        self.model_combo.currentTextChanged.connect(parent.on_model_changed)
        layout.addWidget(self.model_combo)

        layout.addStretch()

        # Right side
        self.auto_btn = QPushButton("🤖 Auto Annotate")
        self.auto_btn.clicked.connect(parent.auto_annotate)

        self.save_btn = QPushButton("💾 Save YOLO")
        self.save_btn.clicked.connect(parent.save_yolo)

        self.train_btn = QPushButton("🚀 Train YOLO")
        self.train_btn.clicked.connect(parent.train_model)
        self.export_btn = QPushButton("📦 Export YOLO")
        self.export_btn.clicked.connect(parent.export_dataset)
        layout.addWidget(self.export_btn)
 

        layout.addWidget(self.auto_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.train_btn)

        # Status label (bottom-right in main window, but we can use sidebar status)