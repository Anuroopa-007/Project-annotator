from pathlib import Path

def create_data_yaml(dataset_path):
    dataset_path = Path(dataset_path)

    classes_file = dataset_path / "classes.txt"
    if not classes_file.exists():
        raise FileNotFoundError("classes.txt not found. Save annotations first.")

    classes = classes_file.read_text().splitlines()

    names_yaml = "\n".join([f"  - {c}" for c in classes])

    content = f"""path: {dataset_path.as_posix()}
train: images/train
val: images/val

nc: {len(classes)}
names:
{names_yaml}
"""

    (dataset_path / "data.yaml").write_text(content)



def save_classes(dataset_path, classes):
    dataset_path = Path(dataset_path)
    classes_file = dataset_path / "classes.txt"

    seen = set()
    ordered_classes = []
    for c in classes:
        if c not in seen:
            seen.add(c)
            ordered_classes.append(c)

    classes_file.write_text("\n".join(ordered_classes))

