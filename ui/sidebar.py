from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QListWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedWidth(250)

        self.setStyleSheet("""
            QWidget { background-color: #2c3e50; color: #ecf0f1; }
            QLabel { color: #ecf0f1; font-size: 14px; }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                text-align: left;
                border: none;
                border-radius: 5px;
                margin: 2px 5px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #34495e;
                margin-top: 10px;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout(self)

        # ===== TITLE =====
        title = QLabel("ACV Annotator")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ===== FILE SECTION =====
        file_group = QGroupBox("File")
        file_layout = QVBoxLayout()

        open_img_btn = QPushButton("📄 Open Image")
        open_img_btn.clicked.connect(self.parent.load_image)

        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.clicked.connect(self.parent.load_folder)

        file_layout.addWidget(open_img_btn)
        file_layout.addWidget(open_folder_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # ===== IMAGE LIST SECTION (PASTE HERE ✅) =====
        image_group = QGroupBox("Images")
        image_layout = QVBoxLayout()

        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.on_image_clicked)

        image_layout.addWidget(self.image_list)
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        # ===== ANNOTATIONS =====
        # ===== ANNOTATIONS =====
        ann_group = QGroupBox("Annotations")
        ann_layout = QVBoxLayout()

        save_btn = QPushButton("💾 Save YOLO")
        save_btn.clicked.connect(self.parent.save_yolo)

        train_btn = QPushButton("🚀 Train YOLO")
        train_btn.clicked.connect(self.parent.train_model)

        ann_layout.addWidget(save_btn)
        ann_layout.addWidget(train_btn)

        ann_group.setLayout(ann_layout)
        layout.addWidget(ann_group)


        # ===== MODELS =====
        model_group = QGroupBox("Models")
        model_layout = QVBoxLayout()

        self.model_combo = QComboBox()
        self.model_combo.addItems(["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"])
        self.model_combo.currentTextChanged.connect(self.parent.on_model_changed)

        auto_btn = QPushButton("🤖 Auto Annotate")
        auto_btn.clicked.connect(self.parent.auto_annotate)

        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(auto_btn)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        layout.addStretch()

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

    # ===== METHODS =====
    def populate_images(self, image_paths):
        self.image_list.clear()
        for path in image_paths:
            self.image_list.addItem(path)

    def on_image_clicked(self, item):
        self.parent.load_image_from_list(item.text())

    def set_status(self, text):
        self.status_label.setText(text)