from pathlib import Path
from shutil import copy2
from PIL import Image

class YOLOExporter:
    @staticmethod
    def export(image_path, annotations, dataset_path, split="train"):
        image_path = Path(image_path)

        images_dir = Path(dataset_path) / "images" / split
        labels_dir = Path(dataset_path) / "labels" / split
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        # Copy image
        copy2(image_path, images_dir / image_path.name)

        # Load image size
        img = Image.open(image_path)
        img_w, img_h = img.size

        # 🔒 Load FIXED class order
        classes = (Path(dataset_path) / "classes.txt").read_text().splitlines()

        lines = []

        for label, rect in annotations:
            label = label.strip().lower()

            if label not in classes:
                raise ValueError(f"Label '{label}' not in classes.txt")

            # ✅ ONLY correct way
            cls_id = classes.index(label)

            x_center = (rect.x() + rect.width() / 2) / img_w
            y_center = (rect.y() + rect.height() / 2) / img_h
            width = rect.width() / img_w
            height = rect.height() / img_h

            lines.append(
                f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            )

        # Save label file
        (labels_dir / f"{image_path.stem}.txt").write_text("\n".join(lines))
