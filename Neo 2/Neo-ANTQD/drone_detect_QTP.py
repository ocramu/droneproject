import cv2
import numpy as np
import Quartz
from Quartz import (
    CGWindowListCreateImage, CGRectNull,
    kCGWindowListOptionIncludingWindow, kCGWindowImageDefault
)

print("Loading YOLO model...")
from ultralytics import YOLO


def find_window(name):
    """Find a window by partial name match, return its window ID and bounds."""
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    matches = []

    for window in window_list:
        owner = window.get('kCGWindowOwnerName', '')
        title = window.get('kCGWindowName', '')
        window_id = window.get('kCGWindowNumber')
        bounds = window.get('kCGWindowBounds')

        if not window_id or not bounds:
            continue

        haystack = f"{owner} {title}".lower()
        if name.lower() in haystack:
            matches.append((window_id, bounds, owner, title))

    if matches:
        # pick the largest matching window
        matches.sort(
            key=lambda x: x[1].get("Width", 0) * x[1].get("Height", 0),
            reverse=True
        )
        return matches[0][0], matches[0][1], matches[0][2], matches[0][3]

    return None, None, None, None


def capture_window(window_id):
    """Capture a window by ID."""
    cg_image = CGWindowListCreateImage(
        CGRectNull,
        kCGWindowListOptionIncludingWindow,
        window_id,
        kCGWindowImageDefault
    )
    if cg_image is None:
        return None

    width = Quartz.CGImageGetWidth(cg_image)
    height = Quartz.CGImageGetHeight(cg_image)
    bytes_per_row = Quartz.CGImageGetBytesPerRow(cg_image)

    provider = Quartz.CGImageGetDataProvider(cg_image)
    data = Quartz.CGDataProviderCopyData(provider)

    arr = np.frombuffer(data, dtype=np.uint8)
    arr = arr.reshape((height, bytes_per_row // 4, 4))
    arr = arr[:, :width, :]  # trim row padding

    return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)


model = YOLO("yolov8n.pt")

# Try QuickTime/iPhone mirroring window first
search_terms = [
    "QuickTime Player",
    "Movie Recording",
    "iPhone"
]

window_id = None
bounds = None
owner = None
title = None

print("Looking for QuickTime/iPhone mirror window...")
for term in search_terms:
    window_id, bounds, owner, title = find_window(term)
    if window_id:
        break

if not window_id:
    print("Mirror window not found. Available windows:")
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    for window in window_list:
        owner_name = window.get('kCGWindowOwnerName', '')
        title_name = window.get('kCGWindowName', '')
        if owner_name or title_name:
            print(f"  - {owner_name}: {title_name}")
    raise SystemExit(1)

print(f"Found window: owner='{owner}', title='{title}', id={window_id}")
print("Starting detection. Press 'q' in the detection window to quit.")

cv2.namedWindow("Drone Detection", cv2.WINDOW_NORMAL)

frame_count = 0
while True:
    frame = capture_window(window_id)
    if frame is None:
        print("Failed to capture mirror window")
        break

    results = model(frame, classes=[0], verbose=False)
    annotated = results[0].plot()

    for box in results[0].boxes:
        conf = float(box.conf[0])
        if conf > 0.5:
            print(f"PERSON DETECTED - Confidence: {conf:.2f}")

    cv2.imshow("Drone Detection", annotated)

    frame_count += 1
    if frame_count == 1:
        print("First frame captured successfully.")

    if (cv2.waitKey(1) & 0xFF) == ord("q"):
        break

cv2.destroyAllWindows()
print(f"Done. Processed {frame_count} frames.")
