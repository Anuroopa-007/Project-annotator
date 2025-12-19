from PyQt5.QtGui import QColor

CLASS_COLORS = {
    "dog": QColor(255, 0, 0),
    "cat": QColor(0, 255, 0),
    "person": QColor(0, 0, 255),
    "bike": QColor(255, 165, 0),
}

def get_color(label):
    return CLASS_COLORS.get(label, QColor(255, 255, 0))
