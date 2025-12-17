from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel

class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)

        self.status = QLabel("Ready")

        self.save_btn = QPushButton("💾 Save")
        self.auto_btn = QPushButton("🤖 Auto Annotate")
        self.export_btn = QPushButton("📤 Export YOLO")

        layout.addWidget(self.status)
        layout.addStretch()
        layout.addWidget(self.save_btn)
        layout.addWidget(self.auto_btn)
        layout.addWidget(self.export_btn)
