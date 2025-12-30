# ui/right_panel.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet("background: #252525; border-left: 1px solid #333;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Objects")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff6200; padding-bottom: 8px;")
        layout.addWidget(title)

        self.objects_list = QListWidget()
        self.objects_list.setStyleSheet("""
            background: #2d2d2d; 
            border: none; 
            border-radius: 8px;
        """)
        layout.addWidget(self.objects_list)

    def update_objects(self, annotations):
        self.objects_list.clear()
        for i, (label, rect) in enumerate(annotations):
            item = QListWidgetItem(f"{i+1}. {label}")
            item.setForeground(QColor("#ffffff"))
            self.objects_list.addItem(item)