# sidebar.py (updated)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont
import os
import math

from ui.themes import THEMES  # Correct import since themes.py is in ui/

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedWidth(300)
        self.current_theme = "dark"  # Default

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title = QLabel("Images")
        title.setFont(QFont('Segoe UI', 16, QFont.Bold))
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        # Image count
        self.count_label = QLabel("0 images")
        self.count_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.count_label)

        # Detected object counts
        self.detect_label = QLabel("Detected:\n—")
        self.detect_label.setAlignment(Qt.AlignLeft)
        self.detect_label.setStyleSheet("background-color: transparent; padding: 12px 0;")
        layout.addWidget(self.detect_label)

        # Thumbnail list
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(280, 158))
        self.image_list.setViewMode(QListWidget.ListMode)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setMovement(QListWidget.Static)
        self.image_list.setSpacing(6)

        self.image_list.itemClicked.connect(self.on_image_clicked)
        layout.addWidget(self.image_list)

        # Pagination
        pag_layout = QHBoxLayout()
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
        self.status_label.setStyleSheet("padding: 12px; font-size: 14px; border-radius: 4px;")
        layout.addWidget(self.status_label)

        # State
        self.all_image_paths = []
        self.current_page = 0
        self.items_per_page = 6
        self.path_to_item = {}

        self.apply_theme(self.current_theme)

    def apply_theme(self, theme_name: str):
        self.current_theme = theme_name
        t = THEMES[theme_name]
        self.setStyleSheet(f"""
            QWidget {{ background-color: {t['bg']}; }}
            QLabel {{ color: {t['text_secondary']}; }}
            QListWidget {{ background-color: {t['surface']}; border: 1px solid {t['border']}; }}
            QListWidget::item:selected {{ background-color: {t['selected']}; }}
            QListWidget::item:hover {{ background-color: {t['surface2']}; }}
            QPushButton {{ background-color: {t['surface']}; color: {t['text']}; }}
            QPushButton:hover {{ background-color: {t['surface2']}; }}
            QPushButton:disabled {{ color: #666; }}
            .status {{ background-color: {t['status']}; color: white; }}
        """)
        self.status_label.setProperty("class", "status")  # For status bg
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    # Rest of methods unchanged...
    # (populate_images, update_page, etc. remain the same)

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

            thumb = pixmap.scaled(280, 158, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            if thumb.width() > 280 or thumb.height() > 158:
                thumb = thumb.copy((thumb.width()-280)//2, (thumb.height()-158)//2, 280, 158)

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
        for cls, num in sorted(counts.items()):
            text += f"• {cls}: {num}\n"

        self.detect_label.setText(text.strip())