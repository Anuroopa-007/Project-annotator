import cv2
import os

def extract_frames(video_path, output_dir, every_n=5):
    cap = cv2.VideoCapture(video_path)
    frame_paths = []

    frame_id = 0
    saved_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % every_n == 0:
            filename = f"frame_{saved_id:06d}.jpg"
            path = os.path.join(output_dir, filename)
            cv2.imwrite(path, frame)
            frame_paths.append(path)
            saved_id += 1

        frame_id += 1

    cap.release()
    return frame_paths
