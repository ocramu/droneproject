import cv2
import numpy as np
import pygetwindow as gw
import dxcam
from ultralytics import YOLO

# --- CONFIGURATION ---
# Common keywords in FPV sim window titles. 
# Update this if your game has a specific title (e.g., "Liftoff", "Uncrashed")
GAME_KEYWORDS = ["FPV", "Kamikaze", "Drone", "Simulator"]
MODEL_PATH = "yolov8n.pt" 
# ---------------------

def find_game_window(keywords):
    """Searches for the game window among active windows."""
    for window in gw.getAllWindows():
        for word in keywords:
            if word.lower() in window.title.lower():
                # Prevent picking up the detection window itself
                if "AI Overlay" in window.title:
                    continue
                return window
    return None

print("Checking for YOLO model...")
model = YOLO(MODEL_PATH)

print("Searching for game window...")
target_window = find_game_window(GAME_KEYWORDS)

if not target_window:
    print("❌ Game window not found! Make sure the game is running.")
    print("Available windows:", [w for w in gw.getAllTitles() if w])
    exit()

print(f"✅ Found: {target_window.title}")

# Initialize DXcam for high-speed capture
# We define the region based on the game window's current position
region = (target_window.left, target_window.top, target_window.right, target_window.bottom)
camera = dxcam.create(region=region, output_color="BGR")

# Create a resizable display window
cv2.namedWindow("AI Overlay", cv2.WINDOW_NORMAL)

print("Starting detection. Press 'q' to quit.")
camera.start(target_fps=60) # Start threaded capture

try:
    while True:
        frame = camera.get_latest_frame()
        if frame is None:
            continue

        # Run AI detection
        # Class 0=person, 2=car, 7=truck (standard military-style targets)
        results = model(frame, classes=[0, 2, 7], verbose=False, conf=0.5)
        
        # Draw boxes on the frame
        annotated_frame = results[0].plot()

        # Check for detections in console
        for box in results[0].boxes:
            conf = float(box.conf[0])
            print(f"TARGET SPOTTED! Confidence: {conf:.2f}")

        cv2.imshow("AI Overlay", annotated_frame)

        # Press 'q' to stop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    camera.stop()
    cv2.destroyAllWindows()
