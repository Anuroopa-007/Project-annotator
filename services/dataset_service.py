from pathlib import Path

def create_data_yaml(dataset_path):
    dataset_path = Path(dataset_path)

    classes = (dataset_path / "classes.txt").read_text().splitlines()

    content = f"""
path: {dataset_path}
train: images
val: images

nc: {len(classes)}
names: {classes}
"""

    (dataset_path / "data.yaml").write_text(content)

def save_classes(dataset_path, classes):
    """
    Saves class names to classes.txt (YOLO standard)
    """
    dataset_path = Path(dataset_path)
    classes_file = dataset_path / "classes.txt"

    # Ensure unique + sorted classes
    unique_classes = sorted(set(classes))

    classes_file.write_text("\n".join(unique_classes))
