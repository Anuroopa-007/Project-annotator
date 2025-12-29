from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QPen, QFont, QColor, QBrush,QPainter
from PyQt5.QtCore import Qt
from utils.colors import get_color


class BBoxItem(QGraphicsRectItem):
    def __init__(self, rect, label):
        super().__init__(rect)
        self.label = label

        # 🎨 Get class-based color
        color = get_color(label)
        if not isinstance(color, QColor):
            color = QColor(255, 255, 0)  # fallback

        # ✅ Border only
        pen = QPen(color)
        pen.setWidth(2)
        pen.setStyle(Qt.SolidLine)
        self.setPen(pen)

        # ✅ NO FILL (CORRECT WAY)
        self.setBrush(QBrush(Qt.NoBrush))

        # Make selectable and movable
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable
        )
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.ItemIsFocusable)
        self.setCursor(Qt.PointingHandCursor)

        # 🏷 Label
        self.text_item = QGraphicsTextItem(label, self)
        self.text_item.setDefaultTextColor(color)

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.text_item.setFont(font)

        self.text_item.setPos(rect.x(), rect.y() - 15)

        # Keep above image
        self.setZValue(10)

    def to_yolo(self, img_w, img_h, class_map=None):
        x_center = (self.rect().x() + self.rect().width() / 2) / img_w
        y_center = (self.rect().y() + self.rect().height() / 2) / img_h
        w = self.rect().width() / img_w
        h = self.rect().height() / img_h

        if class_map is None:
            class_map = {self.label: 0}

        if self.label not in class_map:
            class_map[self.label] = len(class_map)

        cls_id = class_map[self.label]
        return cls_id, x_center, y_center, w, h
    
    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

    # Highlight when selected
        if self.isSelected():
            select_pen = QPen(QColor(0, 122, 204))  # Blue
            select_pen.setWidth(3)
            painter.setPen(select_pen)
            painter.drawRect(self.rect())

