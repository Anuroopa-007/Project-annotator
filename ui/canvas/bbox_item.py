from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QPen, QFont
from PyQt5.QtCore import Qt


class BBoxItem(QGraphicsRectItem):
    def __init__(self, rect, label):
        """
        rect: QRectF for the bounding box
        label: str, class name like 'dog', 'cat', 'human'
        """
        super().__init__(rect)
        self.label = label
        self.setPen(QPen(Qt.red, 2))

        # Add label text
        self.text_item = QGraphicsTextItem(label, self)
        self.text_item.setDefaultTextColor(Qt.red)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.text_item.setFont(font)

        # Position text at top-left of bounding box
        self.text_item.setPos(rect.x(), rect.y() - 15)

    def to_yolo(self, img_w, img_h, class_map=None):
        """
        Convert QRectF to YOLO normalized format (x_center, y_center, w, h)
        Returns: class_id, x_center, y_center, w, h
        """
        x_center = (self.rect().x() + self.rect().width() / 2) / img_w
        y_center = (self.rect().y() + self.rect().height() / 2) / img_h
        w = self.rect().width() / img_w
        h = self.rect().height() / img_h

        # Map label to class_id
        if class_map is None:
            class_map = {self.label: 0}  # default id=0
        if self.label not in class_map:
            class_map[self.label] = len(class_map)
        cls_id = class_map[self.label]

        return cls_id, x_center, y_center, w, h
