import cv2
import pygetwindow as gw
import dxcam
from ultralytics import YOLO
import ctypes

# 1. FIX DPI SCALING: Tells Windows to give us the REAL pixel coordinates
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

# --- CONFIG ---
GAME_KEYWORDS = ["FPV", "Kamikaze", "Drone"]
model = YOLO("yolov8n.pt") 

def find_game_window(keywords):
    for window in gw.getAllWindows():
        if any(word.lower() in window.title.lower() for word in keywords):
            if "AI Overlay" not in window.title:
                return window
    return None

target_window = find_game_window(GAME_KEYWORDS)

if not target_window or target_window.width <= 0:
    print("❌ Game window not found or is minimized!")
    exit()

# 2. CLEAN COORDINATES: DXcam hates negative numbers or zero-width regions
# We ensure the coordinates are within the screen boundaries
left = max(0, target_window.left)
top = max(0, target_window.top)
right = max(left + 100, target_window.right)
bottom = max(top + 100, target_window.bottom)

region = (left, top, right, bottom)
print(f"✅ Capturing Region: {region} for window '{target_window.title}'")

# Initialize Camera
try:
    camera = dxcam.create(output_color="BGR")
    camera.start(region=region, target_fps=30)
except Exception as e:
    print(f"❌ DXcam failed to start: {e}")
    exit()

cv2.namedWindow("AI Overlay", cv2.WINDOW_NORMAL)

try:
    while True:
        frame = camera.get_latest_frame()
        if frame is None:
            continue

        # Resize for speed (The 'Lag' fix from before)
        input_frame = cv2.resize(frame, (416, 416))

        # Run AI (0=person, 2=car, 7=truck)
        results = model.predict(input_frame, classes=[0, 2, 7], conf=0.45, verbose=False, imgsz=416)

        # Show it
        cv2.imshow("AI Overlay", results[0].plot())

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    camera.stop()
    cv2.destroyAllWindows()
