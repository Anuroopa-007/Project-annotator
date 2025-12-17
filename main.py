# main.py
import sys
from PyQt5.QtWidgets import QApplication
from auth.login_window import LoginWindow  # Now this will also use PyQt5

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())