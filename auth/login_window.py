# auth/login_window.py
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt

# Import your original MainWindow (PyQt5)
from ui.main_window import MainWindow

# Path to users JSON
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "storage" / "users.json"


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ACV Annotator - Login")
        self.resize(400, 300)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("ACV Annotator Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Username
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. admin")
        user_layout.addWidget(self.username_input)
        layout.addLayout(user_layout)

        # Password
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        pass_layout.addWidget(self.password_input)
        layout.addLayout(pass_layout)

        # Login Button
        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1f6391; }
        """)
        self.login_btn.clicked.connect(self.check_credentials)
        layout.addWidget(self.login_btn)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; margin-top: 10px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def load_users(self):
        if not USERS_FILE.exists():
            USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            default = [{"username": "admin", "password": "123456"}]
            with open(USERS_FILE, "w") as f:
                json.dump(default, f, indent=4)
            self.users = default
        else:
            try:
                with open(USERS_FILE, "r") as f:
                    self.users = json.load(f)
            except:
                self.users = [{"username": "admin", "password": "123456"}]

    def check_credentials(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.status_label.setText("⚠️ Please fill both fields")
            return

        for user in self.users:
            if user["username"] == username and user["password"] == password:
                self.status_label.setText("✅ Login successful!")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                QApplication.processEvents()
                self.open_main_app()
                return

        self.status_label.setText("❌ Invalid credentials")
        self.password_input.clear()

    def open_main_app(self):
        self.hide()
        self.main_window = MainWindow()  # Your original PyQt5 MainWindow
        self.main_window.show()