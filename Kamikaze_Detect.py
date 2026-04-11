import cv2
import numpy as np
import pygetwindow as gw
import dxcam
from ultralytics import YOLO

# INSTALL BEFORE RUNNING
# pip install ultralytics opencv-python numpy pygetwindow dxcam

# --- CONFIGURATION ---
# Common names for FPV sims: "FPV Military", "Kamikaze Drone", "Liftoff"
GAME_TITLE_KEYWORDS = ["FPV", "Kamikaze", "Drone"]
MODEL_PATH = "yolov8n.pt"  # Nano is best for low latency
# ---------------------

def find_game_window(keywords):
    """Finds the first window that matches keywords."""
    for window in gw.getAllWindows():
        if any(word.lower() in window.title.lower() for word in keywords):
            # Avoid picking up this script's own display window
            if "Detection" in window.title:
                continue
            return window
    return None

print("Loading YOLO model...")
model = YOLO(MODEL_PATH)

print("Searching for FPV Game window...")
target_window = find_game_window(GAME_TITLE_KEYWORDS)

if not target_window:
    print("Could not find the game window. Available windows:")
    for win in gw.getAllTitles():
        if win: print(f" - {win}")
    exit()

print(f"Target Found: {target_window.title}")

# Initialize DXcam for high-performance capture
# We define the 'region' to capture only the game window area
left, top, right, bottom = target_window.left, target_window.top, target_window.right, target_window.bottom
camera = dxcam.create(region=(left, top, right, bottom))

cv2.namedWindow("FPV Detection", cv2.WINDOW_NORMAL)
print("Detection Started. Press 'q' to quit.")

# Start the capture loop
camera.start(target_fps=60) # Threaded capture for performance

try:
    while True:
        # Get the latest frame from the game
        frame = camera.get_latest_frame()
        
        if frame is None:
            continue

        # Convert RGB (DXcam) to BGR (OpenCV)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Detection: 0=person, 2=car, 7=truck (standard YOLO military-like targets)
        results = model(frame_bgr, classes=[0, 2, 7], verbose=False, conf=0.4)
        
        # Draw results
        annotated_frame = results[0].plot()

        cv2.imshow("FPV Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    camera.stop()
    cv2.destroyAllWindows()
