import os
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox


class YOLOExporter:

    @staticmethod
    def export(image_path, annotations):
        if not image_path:
            QMessageBox.warning(None, "Error", "No image loaded")
            return

        if not annotations:
            QMessageBox.warning(None, "Error", "No annotations to save")
            return

        # Load image to get size
        img = QPixmap(image_path)
        img_w, img_h = img.width(), img.height()

        # ✅ Ensure labels folder exists
        labels_dir = os.path.join(os.getcwd(), "labels")
        os.makedirs(labels_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(image_path))[0]
        out_path = os.path.join(labels_dir, f"{base}.txt")

        class_map = {}
        class_id = 0

        with open(out_path, "w") as f:
            for label, rect in annotations:
                if label not in class_map:
                    class_map[label] = class_id
                    class_id += 1

                cid = class_map[label]

                x_center = (rect.x() + rect.width() / 2) / img_w
                y_center = (rect.y() + rect.height() / 2) / img_h
                w = rect.width() / img_w
                h = rect.height() / img_h

                f.write(
                    f"{cid} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n"
                )

        QMessageBox.information(
            None,
            "Saved Successfully ✅",
            f"YOLO file created:\n{out_path}\n\nClasses:\n{class_map}"
        )
