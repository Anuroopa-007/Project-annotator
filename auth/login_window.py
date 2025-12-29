# auth/login_window.py
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QApplication, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QPoint, QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QGraphicsOpacityEffect

from ui.main_window import MainWindow

# ---------------- PATHS ----------------
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "storage" / "users.json"
REMEMBER_FILE = BASE_DIR / "storage" / "remember.json"


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ACV Annotator - Login")
        self.resize(420, 360)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        self.setup_ui()
        self.load_users()
        self.load_remembered_user()
        self.fade_in()

    # =====================================================
    # UI
    # =====================================================
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: white;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #444;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #005a9e; }
            QCheckBox { color: #ccc; }
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #444;
                padding: 6px;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        title = QLabel("ACV Annotator Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Role selector
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "annotator"])
        layout.addWidget(self.role_combo)

        # Remember me
        self.remember_cb = QCheckBox("Remember me")
        layout.addWidget(self.remember_cb)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.check_credentials)
        layout.addWidget(self.login_btn)

        # Spinner (hidden initially)
        self.spinner = QLabel("", self)
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner_movie = QMovie(str(BASE_DIR / "assets" / "spinner.gif"))
        self.spinner.setMovie(self.spinner_movie)
        self.spinner.hide()
        layout.addWidget(self.spinner)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)

    # =====================================================
    # DATA
    # =====================================================
    def load_users(self):
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

        if not USERS_FILE.exists():
            default = [
                {"username": "admin", "password": "123456", "role": "admin"},
                {"username": "user", "password": "123456", "role": "annotator"},
            ]
            USERS_FILE.write_text(json.dumps(default, indent=4))
            self.users = default
        else:
            self.users = json.loads(USERS_FILE.read_text())

    def load_remembered_user(self):
        if REMEMBER_FILE.exists():
            data = json.loads(REMEMBER_FILE.read_text())
            self.username_input.setText(data.get("username", ""))
            self.role_combo.setCurrentText(data.get("role", "annotator"))
            self.remember_cb.setChecked(True)

    def save_remembered_user(self, username, role):
        REMEMBER_FILE.parent.mkdir(parents=True, exist_ok=True)
        REMEMBER_FILE.write_text(json.dumps({
            "username": username,
            "role": role
        }, indent=4))

    # =====================================================
    # ANIMATIONS
    # =====================================================
    def fade_in(self):
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)

        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(700)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def shake_window(self):
        pos = self.pos()
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setKeyValueAt(0, pos)
        anim.setKeyValueAt(0.25, pos + QPoint(-10, 0))
        anim.setKeyValueAt(0.5, pos + QPoint(10, 0))
        anim.setKeyValueAt(0.75, pos + QPoint(-10, 0))
        anim.setKeyValueAt(1, pos)
        anim.start()

    # =====================================================
    # LOGIN LOGIC
    # =====================================================
    def check_credentials(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not username or not password:
            self.status_label.setText("⚠️ Fill all fields")
            return

        # Show spinner
        self.spinner.show()
        self.spinner_movie.start()
        self.login_btn.setEnabled(False)

        QTimer.singleShot(800, lambda: self.verify_user(username, password, role))

    def verify_user(self, username, password, role):
        for user in self.users:
            if (
                user["username"] == username
                and user["password"] == password
                and user["role"] == role
            ):
                if self.remember_cb.isChecked():
                    self.save_remembered_user(username, role)

                self.open_main_app(role)
                return

        self.spinner.hide()
        self.login_btn.setEnabled(True)
        self.status_label.setText("❌ Invalid credentials")
        self.password_input.clear()
        self.shake_window()

    # =====================================================
    # OPEN MAIN APP
    # =====================================================
    def open_main_app(self, role):
        self.spinner.hide()

        # You can pass role later if needed
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
