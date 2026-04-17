import cv2
import numpy as np
from mss import mss
from ultralytics import YOLO
import torch

# --- CONFIG ---
model = YOLO("yolov8n.pt") 
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)

# This defines the screen area (1920x1080)
# mss handles DPI scaling automatically
monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}

print(f"🚀 Starting AI on {device}...")
print("✅ Using MSS Compatibility Mode. Press 'q' to quit.")

with mss() as sct:
    while True:
        # Capture screen
        # sct.grab returns a raw pixels object
        screenshot = sct.grab(monitor)
        
        # Convert to numpy array and then to BGR for OpenCV
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        # 1. SCALE DOWN (The Speed Fix)
        # We shrink the 1080p frame to 416 for the AI
        input_frame = cv2.resize(frame, (416, 416))

        # 2. RUN AI DETECTION
        results = model.predict(
            input_frame, 
            classes=[0, 2, 7], 
            conf=0.45, 
            verbose=False, 
            imgsz=416,
            half=(device == 'cuda')
        )

        # 3. SHOW THE RESULT
        # result[0].plot() draws the boxes on the 416x416 frame
        annotated_frame = results[0].plot()
        
        cv2.imshow("FPV AI Overlay", annotated_frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
