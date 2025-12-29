from pathlib import Path
import shutil
from PyQt5.QtWidgets import QFileDialog, QMessageBox


def export_yolo_dataset(parent, dataset_path):
    """
    Export YOLO dataset (images + labels + data.yaml)
    """

    dataset_path = Path(dataset_path)

    images_dir = dataset_path / "images"
    labels_dir = dataset_path / "labels"
    data_yaml = dataset_path / "data.yaml"

    if not images_dir.exists() or not labels_dir.exists():
        QMessageBox.warning(parent, "Export Failed", "No YOLO data found to export.")
        return

    # Ask user where to export
    export_root = QFileDialog.getExistingDirectory(
        parent,
        "Select Export Folder"
    )
    if not export_root:
        return

    export_root = Path(export_root) / "yolo_export"
    export_root.mkdir(parents=True, exist_ok=True)

    # Copy folders
    shutil.copytree(images_dir, export_root / "images", dirs_exist_ok=True)
    shutil.copytree(labels_dir, export_root / "labels", dirs_exist_ok=True)

    # Copy data.yaml
    if data_yaml.exists():
        shutil.copy(data_yaml, export_root / "data.yaml")

    QMessageBox.information(
        parent,
        "Export Complete",
        f"YOLO dataset exported to:\n{export_root}"
    )
