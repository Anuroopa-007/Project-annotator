from PyQt5.QtGui import QColor

CLASS_COLORS = {
    "person": QColor(0, 128, 255),  # Softer blue
    "car": QColor(0, 255, 128),     # Lighter green
    "bus": QColor(255, 193, 7),     # Amber
    "truck": QColor(220, 53, 69),   # Reddish
    "bike": QColor(134, 48, 167),   # Purple
    "dog": QColor(153, 102, 51),    # Brownish
}

def get_color(label):
    return CLASS_COLORS.get(label.lower(), QColor(255, 193, 7))  # Default amber