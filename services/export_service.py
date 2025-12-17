from pathlib import Path
import shutil


def create_data_yaml(dataset_path, class_names):
    content = f"""
path: {dataset_path}
train: images/train
val: images/val

nc: {len(class_names)}
names: {class_names}
"""
    with open(dataset_path / "data.yaml", "w") as f:
        f.write(content)
def export_yolo_dataset(dataset_path):
    dataset_path = Path(dataset_path)
    export_dir = dataset_path / "exports" / "yolo"
    export_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(dataset_path / "images", export_dir / "images", dirs_exist_ok=True)
    shutil.copytree(dataset_path / "annotations", export_dir / "labels", dirs_exist_ok=True)

