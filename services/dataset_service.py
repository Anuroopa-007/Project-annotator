from pathlib import Path

def load_classes(dataset_path):
    path = Path(dataset_path) / "classes.txt"
    if not path.exists():
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]
