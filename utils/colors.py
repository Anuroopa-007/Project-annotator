from PyQt5.QtGui import QColor

CLASS_COLORS = {
    "person": QColor(0, 0, 255),
    "car": QColor(0, 255, 0),
    "bus": QColor(255, 165, 0),
    "truck": QColor(255, 0, 0),
    "bike": QColor(128, 0, 128),
    "dog": QColor(139, 69, 19),
}

def get_color(label):
    return CLASS_COLORS.get(label.lower(), QColor(255, 255, 0))
