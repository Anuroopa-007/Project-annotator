# sidebar.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
import os
import math


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #ffffff; }
            QLabel { color: #aaa; font-size: 13px; padding: 10px; }
            QListWidget {
                background-color: #252526;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                border-left: 4px solid #007acc;
            }
            QListWidget::item:hover {
                background-color: #2d2d30;
            }
            QPushButton {
                background-color: #333;
                color: #ccc;
                border: none;
                padding: 8px;
            }
            QPushButton:hover { background-color: #444; }
            QPushButton:disabled { color: #666; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("Images")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 20px 15px 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Image count
        self.count_label = QLabel("0 images")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("color: #888; padding-bottom: 10px;")
        layout.addWidget(self.count_label)
        # Detected object counts
        self.detect_label = QLabel("Detected:\n—")
        self.detect_label.setAlignment(Qt.AlignLeft)
        self.detect_label.setStyleSheet("""
            padding: 10px 15px;
            font-size: 13px;
            color: #ddd;
        """)
        layout.addWidget(self.detect_label)


        # Thumbnail list
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(240, 135))  # Wide thumbnails
        self.image_list.setViewMode(QListWidget.ListMode)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setMovement(QListWidget.Static)
        self.image_list.setSpacing(0)

        self.image_list.itemClicked.connect(self.on_image_clicked)
        layout.addWidget(self.image_list)

        # Pagination
        pag_layout = QHBoxLayout()
        pag_layout.setContentsMargins(10, 10, 10, 10)

        self.prev_btn = QPushButton("◀ Previous")
        self.next_btn = QPushButton("Next ▶")
        self.page_label = QLabel("1 / 1")

        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)

        pag_layout.addWidget(self.prev_btn)
        pag_layout.addStretch()
        pag_layout.addWidget(self.page_label)
        pag_layout.addStretch()
        pag_layout.addWidget(self.next_btn)

        layout.addLayout(pag_layout)

        # Bottom status
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background-color: #007acc; padding: 10px; font-size: 13px;")
        layout.addWidget(self.status_label)

        # State
        self.all_image_paths = []
        self.current_page = 0
        self.items_per_page = 6
        self.path_to_item = {}

    def populate_images(self, image_paths):
        self.all_image_paths = image_paths
        self.path_to_item.clear()
        self.current_page = 0
        self.count_label.setText(f"{len(image_paths)} images")
        self.update_page()

        if image_paths:
            self.parent.load_image_from_list(image_paths[0])

    def update_page(self):
        self.image_list.clear()
        self.path_to_item.clear()

        total_pages = max(1, math.ceil(len(self.all_image_paths) / self.items_per_page))
        self.page_label.setText(f"{self.current_page + 1} / {total_pages}")

        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_paths = self.all_image_paths[start:end]

        for path in page_paths:
            filename = os.path.basename(path)
            pixmap = QPixmap(path)
            if pixmap.isNull():
                continue

            thumb = pixmap.scaled(240, 135, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            if thumb.width() > 240 or thumb.height() > 135:
                thumb = thumb.copy((thumb.width()-240)//2, (thumb.height()-135)//2, 240, 135)

            icon = QIcon(thumb)
            item = QListWidgetItem(icon, filename)
            item.setData(Qt.UserRole, path)
            item.setTextAlignment(Qt.AlignCenter)

            self.image_list.addItem(item)
            self.path_to_item[path] = item

        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(end < len(self.all_image_paths))

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def next_page(self):
        if (self.current_page + 1) * self.items_per_page < len(self.all_image_paths):
            self.current_page += 1
            self.update_page()

    def on_image_clicked(self, item):
        path = item.data(Qt.UserRole)
        self.parent.load_image_from_list(path)

    def set_status(self, text):
        self.status_label.setText(text)

    def highlight_current_image(self, current_path):
        if current_path in self.path_to_item:
            item = self.path_to_item[current_path]
            self.image_list.setCurrentItem(item)
            self.image_list.scrollToItem(item)

    def update_detection_counts(self, counts: dict):
        """
        counts example:
        {
            'car': 3,
            'bike': 1,
            'truck': 2
        }
        """
        if not counts:
            self.detect_label.setText("Detected:\n—")
            return

        text = "Detected:\n"
        for cls, num in counts.items():
            text += f"{cls}: {num}\n"

        self.detect_label.setText(text.strip())
