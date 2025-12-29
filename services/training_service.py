
def train_yolo(data_yaml, base_model, output_dir):
    from ultralytics import YOLO

    model = YOLO(base_model)
    model.train(
        data=data_yaml,
        epochs=30,
        imgsz=640,
        project=output_dir,
        name="v1"
    )
