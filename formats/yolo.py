from pathlib import Path
from shutil import copy2
from PIL import Image
from services.dataset_service import save_classes

class YOLOExporter:
    @staticmethod
    def export(image_path, annotations, dataset_path, split="train"):
        """
        image_path: path to image file
        annotations: [(label, QRectF), ...]
        dataset_path: storage/datasets/<dataset_name>
        split: 'train' or 'val'
        """

        image_path = Path(image_path)

        # --- Create folders ---
        images_dir = Path(dataset_path) / "images" / split
        labels_dir = Path(dataset_path) / "labels" / split
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        # --- Copy image to images folder ---
        dest_image_path = images_dir / image_path.name
        if not dest_image_path.exists():
            copy2(image_path, dest_image_path)

        # --- Load image size ---
        img = Image.open(image_path)
        img_w, img_h = img.size

        # --- Prepare labels ---
        class_names = []
        class_map = {}
        lines = []

        for label, rect in annotations:
            if label not in class_map:
                class_map[label] = len(class_map)
                class_names.append(label)

            cls_id = class_map[label]

            # Normalize coordinates 0-1
            x_center = (rect.x() + rect.width() / 2) / img_w
            y_center = (rect.y() + rect.height() / 2) / img_h
            width = rect.width() / img_w
            height = rect.height() / img_h

            lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        # --- Save label file ---
        label_path = labels_dir / f"{image_path.stem}.txt"
        label_path.write_text("\n".join(lines))

        # --- Save classes.txt once ---
        save_classes(dataset_path, class_names)
