import cv2
import dxcam
from ultralytics import YOLO
import torch
import ctypes

# 1. FIX DPI (Critical for 1920x1080 accuracy)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()

# --- CONFIG ---
model = YOLO("yolov8n.pt") 
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)

print(f"🚀 Initializing at 1920x1080 on {device}...")

# 2. Capture the FULL SCREEN (No region math = no 'Invalid Region' error)
camera = dxcam.create(output_color="BGR")

# We start the camera without a 'region' to default to the primary monitor
camera.start(target_fps=30) 

cv2.namedWindow("AI Overlay", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AI Overlay", 960, 540) # Smaller preview window to save space

print("✅ AI is watching the whole screen. Press 'q' to quit.")

try:
    while True:
        frame = camera.get_latest_frame()
        if frame is None:
            continue

        # 3. FAST RESIZE: Scale the 1080p frame down to 416 for the AI
        # This keeps the lag low even while capturing the whole screen
        input_frame = cv2.resize(frame, (416, 416))

        # 4. RUN DETECTION
        results = model.predict(
            input_frame, 
            classes=[0, 2, 7], 
            conf=0.45, 
            verbose=False, 
            imgsz=416,
            half=(device == 'cuda') 
        )

        # 5. DISPLAY
        # We show the 416x416 detection window so it doesn't cover your game
        cv2.imshow("AI Overlay", results[0].plot())

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    camera.stop()
    cv2.destroyAllWindows()
