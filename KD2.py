import cv2
import numpy as np
import pygetwindow as gw
import dxcam
from ultralytics import YOLO
import torch

# --- CONFIG ---
GAME_KEYWORDS = ["FPV", "Kamikaze", "Drone"]
# Use the "Nano" version for maximum speed
model = YOLO("yolov8n.pt") 

# Automatically use GPU if you have an NVIDIA card
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
print(f"Running on: {device}")

def find_game_window(keywords):
    for window in gw.getAllWindows():
        if any(word.lower() in window.title.lower() for word in keywords):
            if "AI Overlay" not in window.title:
                return window
    return None

target_window = find_game_window(GAME_KEYWORDS)

if not target_window:
    print("❌ Game window not found!")
    exit()

# Set up capture region
region = (target_window.left, target_window.top, target_window.right, target_window.bottom)
camera = dxcam.create(region=region, output_color="BGR")

# Performance optimization: Start capture at 30 FPS to save CPU
camera.start(target_fps=30)

cv2.namedWindow("AI Overlay", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AI Overlay", 800, 600)

print("Starting Fast Detection. Press 'q' to quit.")

frame_count = 0

try:
    while True:
        frame = camera.get_latest_frame()
        if frame is None:
            continue

        frame_count += 1
        # Skip every other frame to keep the game smooth
        if frame_count % 2 != 0:
            continue

        # 1. Resize to 416px for a massive speed boost
        # YOLOv8 processes smaller images much faster than 1080p
        input_frame = cv2.resize(frame, (416, 416))

        # 2. Run detection (0=person, 2=car, 7=truck)
        # stream=True is more memory efficient
        results = model.predict(
            source=input_frame, 
            classes=[0, 2, 7], 
            conf=0.45, 
            verbose=False, 
            imgsz=416,
            half=True if device == 'cuda' else False # Use FP16 if on GPU
        )

        # 3. Render and Display
        annotated_frame = results[0].plot()
        cv2.imshow("AI Overlay", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    camera.stop()
    cv2.destroyAllWindows()
