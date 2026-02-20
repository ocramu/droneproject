import cv2
import numpy as np
import Quartz
from Quartz import (
    CGWindowListCreateImage, CGRectNull,
    kCGWindowListOptionIncludingWindow, kCGWindowImageDefault
)

# Import YOLO after other imports (it does network checks)
print("Loading YOLO model (this may take a moment)...")
from ultralytics import YOLO

def find_window(name):
    """Find a window by partial name match, return its window ID and bounds."""
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    for window in window_list:
        owner = window.get('kCGWindowOwnerName', '')
        title = window.get('kCGWindowName', '')
        if name.lower() in owner.lower() or name.lower() in title.lower():
            window_id = window.get('kCGWindowNumber')
            bounds = window.get('kCGWindowBounds')
            if window_id and bounds:
                return window_id, bounds
    return None, None

def capture_window(window_id):
    """Capture a window by ID (works even if window is behind others)."""
    cg_image = CGWindowListCreateImage(
        CGRectNull,
        kCGWindowListOptionIncludingWindow,
        window_id,
        kCGWindowImageDefault
    )
    if cg_image is None:
        return None

    # Get image dimensions
    width = Quartz.CGImageGetWidth(cg_image)
    height = Quartz.CGImageGetHeight(cg_image)
    bytes_per_row = Quartz.CGImageGetBytesPerRow(cg_image)

    # Get pixel data
    provider = Quartz.CGImageGetDataProvider(cg_image)
    data = Quartz.CGDataProviderCopyData(provider)

    # Convert to numpy array
    arr = np.frombuffer(data, dtype=np.uint8)
    arr = arr.reshape((height, bytes_per_row // 4, 4))
    arr = arr[:, :width, :]  # Trim padding

    # Convert BGRA to BGR
    return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

# Load YOLOv8 model
model = YOLO("yolov8n.pt")

# Find BlueStacks window
print("Looking for BlueStacks window...")
window_id, bounds = find_window("BlueStacks")

if not window_id:
    print("BlueStacks window not found! Available windows:")
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    for window in window_list:
        owner = window.get('kCGWindowOwnerName', '')
        title = window.get('kCGWindowName', '')
        if owner and title:
            print(f"  - {owner}: {title}")
    exit(1)

print(f"Found BlueStacks (window ID: {window_id})")
print("Starting capture. Press 'q' in the detection window to quit.")
print("You can now put the detection window in front - BlueStacks can be behind it.")

# Create window first (helps with macOS display issues)
cv2.namedWindow("Drone Detection", cv2.WINDOW_NORMAL)

frame_count = 0
while True:
    # Capture the BlueStacks window directly (works even if behind other windows)
    frame = capture_window(window_id)

    if frame is None:
        print("Failed to capture window")
        break

    # Run detection for 'person' class only
    results = model(frame, classes=[0], verbose=False)
    annotated = results[0].plot()

    for box in results[0].boxes:
        conf = float(box.conf[0])
        if conf > 0.5:
            print(f"PERSON DETECTED - Confidence: {conf:.2f}")

    cv2.imshow("Drone Detection", annotated)

    frame_count += 1
    if frame_count == 1:
        print("First frame captured. You can now fullscreen this window!")

    # Wait 1ms and check for 'q' key
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()
print(f"Done. Processed {frame_count} frames.")
