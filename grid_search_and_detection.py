from pynput import keyboard, mouse as pynput_mouse
from pynput.mouse import Controller as MouseController, Button
import time
import threading
import Quartz
import numpy as np
from ultralytics import YOLO
from Quartz import (CGWindowListCreateImage, kCGWindowImageDefault,
                     CGRectNull, kCGWindowListOptionIncludingWindow)
import cv2

mouse = MouseController()

# --- CONFIGURATION ---
MIRROR_WINDOW_NAME = "iPhone Mirroring"
JOYSTICK_SENSITIVITY = 0.15  # Distance to drag to reach joystick edge
DRONE_SPEED_FPS = 6.008       # Estimated feet per second (ADJUST THIS)
GRID_SIZE_FT = 25            # 25ft boundary
LANE_WIDTH_FT = 12          # Distance between each "pass"
YAW_TIME_90 = 1.7            # Seconds to hold yaw for a 90° turn (ADJUST THIS)
YOLO_CONFIDENCE = 0.30        # Minimum confidence to count as a person detection
YOLO_HOLD_TIME = 2.0          # Seconds of continuous detection before triggering stop
YOLO_CHECK_INTERVAL = 0.2     # Seconds between each YOLO frame check

# --- APPROACH MODE CONFIG ---
APPROACH_NUDGE_TIME = 0.3     # Duration of each yaw/pitch correction nudge (seconds)
APPROACH_DESCEND_TIME = 0.5   # Duration of each descent step
CENTER_DEADZONE = 0.15        # Person must be within 15% of frame center to count as centered
APPROACH_BBOX_TARGET = 0.20   # Stop when person bbox fills 20% of frame area
APPROACH_MAX_LOST = 10.0      # Seconds of spinning without finding person before aborting
APPROACH_SPIN_TIME = 0.4      # Duration of each spin nudge when searching for lost person
PREVIEW_SCALE = 0.4           # Scale factor for the YOLO preview window

# --- CALIBRATION STATE ---
TAKEOFF_CENTER = [0.50, 0.72]
L_JOY_NORM = [0.28, 0.78]
R_JOY_NORM = [0.72, 0.78]

bounds = None
active_keys = set()
calibrating = False
calibration_step = 0
waiting_for_click = False
grid_running = False
kill_grid = False
person_detected = False
yolo_model = None
approach_running = False
kill_approach = False
yolo_triggered = False
latest_display_frame = None
frame_lock = threading.Lock()

def find_mirror_window():
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
    )
    for window in window_list:
        owner = window.get("kCGWindowOwnerName", "")
        title = window.get("kCGWindowName", "")
        if MIRROR_WINDOW_NAME.lower() in owner.lower() or MIRROR_WINDOW_NAME.lower() in title.lower():
            window_id = window.get("kCGWindowNumber")
            bounds = window.get("kCGWindowBounds")
            if window_id and bounds:
                return window_id, bounds
    return None, None

def refresh_bounds():
    global bounds
    _, new_bounds = find_mirror_window()
    if new_bounds:
        bounds = new_bounds

def to_screen_coords(norm_pos):
    x = bounds['X'] + norm_pos[0] * bounds['Width']
    y = bounds['Y'] + norm_pos[1] * bounds['Height']
    return int(x), int(y)

def to_normalized(pos):
    x = (pos[0] - bounds['X']) / bounds['Width']
    y = (pos[1] - bounds['Y']) / bounds['Height']
    return [x, y]

def get_dynamic_positions():
    takeoff = to_screen_coords(TAKEOFF_CENTER)
    l_joy = to_screen_coords(L_JOY_NORM)
    r_joy = to_screen_coords(R_JOY_NORM)
    drag_dist = int(bounds['Width'] * JOYSTICK_SENSITIVITY)
    return takeoff, l_joy, r_joy, drag_dist

# --- FLIGHT PRIMITIVES ---
def interruptible_sleep(duration):
    """Sleep in small increments, return False if any killswitch triggered."""
    start = time.time()
    while time.time() - start < duration:
        if kill_grid or kill_approach:
            return False
        time.sleep(0.05)
    return True

def hold_joystick(start_pos, direction, drag_dist, duration):
    """Drags joystick in a direction and holds it for a specific time.
    Returns False if interrupted by killswitch."""
    global kill_grid
    target_pos = list(start_pos)
    if direction == 'forward':  target_pos[1] -= drag_dist
    elif direction == 'back':   target_pos[1] += drag_dist
    elif direction == 'left':   target_pos[0] -= drag_dist
    elif direction == 'right':  target_pos[0] += drag_dist

    mouse.position = start_pos
    time.sleep(0.05)
    mouse.press(Button.left)

    # Smooth drag to target
    steps = 5
    for i in range(1, steps + 1):
        mouse.position = (
            start_pos[0] + int((target_pos[0] - start_pos[0]) * i / steps),
            start_pos[1] + int((target_pos[1] - start_pos[1]) * i / steps)
        )
        time.sleep(0.01)

    if not interruptible_sleep(duration):
        mouse.release(Button.left)
        return False
    mouse.release(Button.left)
    time.sleep(0.5)
    return not kill_grid

def run_grid_search():
    """Executes a 10x10ft lawnmower pattern with turns. Press SPACE to abort."""
    global grid_running, kill_grid
    grid_running = True
    kill_grid = False

    print(f"\n!!! STARTING GRID SEARCH ({GRID_SIZE_FT}ft x {GRID_SIZE_FT}ft) !!!")
    print("Press SPACEBAR to abort and return to manual controls.\n")
    refresh_bounds()
    _, L_JOY, R_JOY, DRAG_DIST = get_dynamic_positions()

    travel_time = GRID_SIZE_FT / DRONE_SPEED_FPS
    lane_time = LANE_WIDTH_FT / DRONE_SPEED_FPS
    num_lanes = int(GRID_SIZE_FT / LANE_WIDTH_FT)

    print(f"  Lane length: {GRID_SIZE_FT}ft = {travel_time:.1f}s forward")
    print(f"  Lane spacing: {LANE_WIDTH_FT}ft = {lane_time:.1f}s advance")
    print(f"  Lanes: {num_lanes + 1}, Turn time: {YAW_TIME_90}s\n")

    for i in range(num_lanes + 1):
        if kill_grid:
            break

        # Fly forward (always forward since drone turns at corners)
        print(f"Lane {i+1}/{num_lanes+1}: Flying Forward...")
        if not hold_joystick(R_JOY, 'forward', DRAG_DIST, travel_time):
            break

        if i < num_lanes:
            # Alternate turn direction: even lanes turn right, odd lanes turn left
            if i % 2 == 0:
                turn_dir = 'right'
            else:
                turn_dir = 'left'

            # Turn 90° at end of lane
            print(f"Turning {turn_dir} 90°...")
            if not hold_joystick(L_JOY, turn_dir, DRAG_DIST, YAW_TIME_90):
                break

            # Move forward one lane width
            print("Advancing to next lane...")
            if not hold_joystick(R_JOY, 'forward', DRAG_DIST, lane_time):
                break

            # Turn another 90° same direction to face back down the grid
            print(f"Turning {turn_dir} 90°...")
            if not hold_joystick(L_JOY, turn_dir, DRAG_DIST, YAW_TIME_90):
                break

    grid_running = False
    if kill_grid:
        kill_grid = False
        if yolo_triggered:
            print("\n--- GRID SEARCH STOPPED: PERSON DETECTED --- Starting approach...")
            thread = threading.Thread(target=run_approach, daemon=True)
            thread.start()
        else:
            print("\n--- GRID SEARCH ABORTED --- Manual controls active.")
    else:
        print("\n--- GRID SEARCH COMPLETE --- Manual controls active.")

# --- APPROACH MODE ---
def get_best_person(results, frame_w, frame_h):
    """Get highest-confidence person bbox. Returns (cx, cy, area_fraction) normalized 0-1, or None."""
    best = None
    best_conf = 0
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0 and float(box.conf[0]) >= YOLO_CONFIDENCE:
                conf = float(box.conf[0])
                if conf > best_conf:
                    best_conf = conf
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx = ((x1 + x2) / 2) / frame_w
                    cy = ((y1 + y2) / 2) / frame_h
                    bbox_area = (x2 - x1) * (y2 - y1)
                    area_fraction = bbox_area / (frame_w * frame_h)
                    best = (cx, cy, area_fraction)
    return best

def run_approach():
    """Centers the person in frame and descends to get closer.
    If person is lost, spins to find them again."""
    global approach_running, kill_approach, yolo_triggered
    approach_running = True
    kill_approach = False

    print("\n!!! APPROACH MODE — Centering and descending !!!")
    print("Press SPACEBAR to abort and return to manual controls.\n")

    refresh_bounds()
    _, L_JOY, R_JOY, DRAG_DIST = get_dynamic_positions()
    window_id, _ = find_mirror_window()

    if window_id is None:
        print("[APPROACH] ERROR: Window not found. Aborting.")
        approach_running = False
        yolo_triggered = False
        return

    last_seen = time.time()
    last_known_dir = 'right'  # Which way the person was last seen drifting

    while not kill_approach:
        frame = capture_window(window_id)
        if frame is None:
            time.sleep(0.1)
            continue

        frame_h, frame_w = frame.shape[:2]
        results = yolo_model(frame, verbose=False)
        person = get_best_person(results, frame_w, frame_h)

        if person is None:
            elapsed = time.time() - last_seen
            if elapsed > APPROACH_MAX_LOST:
                print(f"[APPROACH] Person lost for {APPROACH_MAX_LOST}s. Aborting.")
                update_preview(frame, results, "APPROACH | LOST - Aborting")
                break
            # Spin in the last known direction to find person
            print(f"[APPROACH] Person lost — spinning {last_known_dir}... ({elapsed:.1f}s / {APPROACH_MAX_LOST}s)")
            update_preview(frame, results, f"APPROACH | Searching {last_known_dir}...")
            hold_joystick(L_JOY, last_known_dir, DRAG_DIST, APPROACH_SPIN_TIME)
            if kill_approach:
                break
            continue

        last_seen = time.time()
        cx, cy, area = person

        # Track which side the person is on for spin search
        if cx > 0.5:
            last_known_dir = 'right'
        else:
            last_known_dir = 'left'

        # Check if close enough
        if area >= APPROACH_BBOX_TARGET:
            print(f"[APPROACH] Person fills {area*100:.0f}% of frame — close enough!")
            update_preview(frame, results, f"APPROACH | COMPLETE ({area*100:.0f}%)")
            break

        h_offset = cx - 0.5

        # Horizontal centering (yaw) — keep person centered left/right
        if abs(h_offset) > CENTER_DEADZONE:
            direction = 'right' if h_offset > 0 else 'left'
            print(f"[APPROACH] Yawing {direction} (offset: {h_offset:+.2f})")
            update_preview(frame, results, f"APPROACH | Yaw {direction} ({area*100:.0f}%)")
            hold_joystick(L_JOY, direction, DRAG_DIST, APPROACH_NUDGE_TIME)
            if kill_approach:
                break

        # Horizontally centered — descend to get closer
        else:
            print(f"[APPROACH] Centered! Descending... (person area: {area*100:.0f}%)")
            update_preview(frame, results, f"APPROACH | Descending ({area*100:.0f}%)")
            hold_joystick(L_JOY, 'back', DRAG_DIST, APPROACH_DESCEND_TIME)
            if kill_approach:
                break

        time.sleep(0.1)

    approach_running = False
    yolo_triggered = False
    if kill_approach:
        kill_approach = False
        print("\n--- APPROACH ABORTED --- Manual controls active.")
    else:
        print("\n--- APPROACH COMPLETE --- Manual controls active.")

# --- YOLO PERSON DETECTION ---
def capture_window(window_id):
    """Capture the iPhone Mirroring window as a numpy array."""
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
    pixel_data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(cg_image))

    img_array = np.frombuffer(pixel_data, dtype=np.uint8)
    img_array = img_array.reshape((height, bytes_per_row // 4, 4))
    img_array = img_array[:height, :width, :3]  # Drop alpha, trim padding
    img_array = img_array[:, :, ::-1]  # BGRA -> RGB (drop A already done)
    return img_array.copy()

def draw_detections(frame, results, status_text=""):
    """Draw YOLO bounding boxes and status on frame. Returns BGR image for cv2."""
    display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    h, w = display.shape[:2]
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0 and float(box.conf[0]) >= YOLO_CONFIDENCE:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display, f"Person {conf:.0%}", (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    # Draw crosshair at center
    cx, cy = w // 2, h // 2
    cv2.line(display, (cx - 15, cy), (cx + 15, cy), (0, 0, 255), 1)
    cv2.line(display, (cx, cy - 15), (cx, cy + 15), (0, 0, 255), 1)
    # Status text
    if status_text:
        cv2.putText(display, status_text, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    # Resize for small preview
    small = cv2.resize(display, (int(w * PREVIEW_SCALE), int(h * PREVIEW_SCALE)))
    return small

def run_display_loop():
    """Shows the YOLO preview window. MUST run on main thread (macOS requirement)."""
    global latest_display_frame
    while True:
        with frame_lock:
            frame = latest_display_frame
        if frame is not None:
            cv2.imshow("YOLO Detection", frame)
        cv2.waitKey(30)

def update_preview(frame, results, status_text=""):
    """Update the shared display frame."""
    global latest_display_frame
    display = draw_detections(frame, results, status_text)
    with frame_lock:
        latest_display_frame = display

def run_yolo_watcher():
    """Background thread: watches iPhone Mirroring window for people.
    Triggers killswitch after 2 continuous seconds of detection."""
    global kill_grid, person_detected, yolo_model, yolo_triggered

    print("[YOLO] Loading YOLOv8 model...")
    yolo_model = YOLO("yolov8n.pt")
    print("[YOLO] Model loaded. Detection active.")

    continuous_start = None

    while True:
        if not grid_running:
            continuous_start = None
            person_detected = False
            # Still grab frames to keep preview alive when idle
            window_id, _ = find_mirror_window()
            if window_id:
                frame = capture_window(window_id)
                if frame is not None:
                    results = yolo_model(frame, verbose=False)
                    update_preview(frame, results, "IDLE | Waiting for grid search (G)")
            time.sleep(0.5)
            continue

        window_id, _ = find_mirror_window()
        if window_id is None:
            time.sleep(YOLO_CHECK_INTERVAL)
            continue

        frame = capture_window(window_id)
        if frame is None:
            time.sleep(YOLO_CHECK_INTERVAL)
            continue

        results = yolo_model(frame, verbose=False)
        found_person = False
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0 and float(box.conf[0]) >= YOLO_CONFIDENCE:
                    found_person = True
                    break
            if found_person:
                break

        if found_person:
            person_detected = True
            if continuous_start is None:
                continuous_start = time.time()
                print("[YOLO] Person detected, watching...")
            elapsed = time.time() - continuous_start
            update_preview(frame, results, f"GRID SEARCH | Person: {elapsed:.1f}s / {YOLO_HOLD_TIME}s")
            if elapsed >= YOLO_HOLD_TIME:
                print(f"\n[YOLO] PERSON CONFIRMED for {YOLO_HOLD_TIME}s! Stopping grid search!")
                yolo_triggered = True
                kill_grid = True
                mouse.release(Button.left)
                continuous_start = None
        else:
            if continuous_start is not None:
                print("[YOLO] Person lost, timer reset.")
            continuous_start = None
            person_detected = False
            update_preview(frame, results, "GRID SEARCH | Scanning...")

        time.sleep(YOLO_CHECK_INTERVAL)

# --- HANDLERS ---
def on_click(x, y, button, pressed):
    global calibration_step, calibrating, waiting_for_click
    global TAKEOFF_CENTER, L_JOY_NORM, R_JOY_NORM

    if not calibrating or not pressed or not waiting_for_click:
        return

    refresh_bounds()
    norm = to_normalized((x, y))

    if calibration_step == 0:
        TAKEOFF_CENTER[:] = norm
        print(f"[Calib] Takeoff set: {norm}")
    elif calibration_step == 1:
        L_JOY_NORM[:] = norm
        print(f"[Calib] Left joystick set: {norm}")
    elif calibration_step == 2:
        R_JOY_NORM[:] = norm
        print(f"[Calib] Right joystick set: {norm}")
        print("Calibration complete ✅")
        calibrating = False

    waiting_for_click = False 
    calibration_step += 1
    if calibrating:
        print(f"Saved. Press 'C' for Step {calibration_step + 1}.")

def process_key_press(key):
    global calibrating, calibration_step, waiting_for_click, kill_grid, kill_approach
    try:
        if hasattr(key, 'char') and key.char:
            k = key.char.lower()
        else:
            k = key.name

        if k == 'space' and (grid_running or approach_running):
            kill_grid = True
            kill_approach = True
            mouse.release(Button.left)
            mode = "approach" if approach_running else "grid search"
            print(f"\n[KILLSWITCH] Stopping {mode}...")
            return

        if k == 'c':
            if not calibrating:
                calibrating = True
                calibration_step = 0
                print("\n--- CALIBRATION MODE ---")
            waiting_for_click = True 
            prompts = ["TAKEOFF/LAND", "LEFT joystick", "RIGHT joystick"]
            if calibration_step < 3:
                print(f"Step {calibration_step+1}: Click {prompts[calibration_step]}...")
            return

        if k == 'g' and not grid_running:
            thread = threading.Thread(target=run_grid_search, daemon=True)
            thread.start()
            return

        if calibrating: return

        # Manual overrides (standard flight)
        refresh_bounds()
        takeoff, L_JOY, R_JOY, DRAG_DIST = get_dynamic_positions()
        # ... [Manual flight logic same as previous script] ...

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("--- Drone Grid Search Controller + YOLO Detection ---")
    print("1. Press 'C' (3 times) to calibrate centers.")
    print("2. Fly to your starting corner manually.")
    print(f"3. Press 'G' to start the {GRID_SIZE_FT}ft x {GRID_SIZE_FT}ft grid search.")
    print("4. Press SPACEBAR to abort grid search or approach.")
    print(f"5. YOLO auto-stops grid if person detected for {YOLO_HOLD_TIME}s (>{YOLO_CONFIDENCE} confidence).")
    print("6. After YOLO detection, drone auto-centers and descends toward person.")

    window_id, bounds = find_mirror_window()
    if not window_id:
        print("ERROR: iPhone Mirroring window not found!")
        exit(1)

    mouse_listener = pynput_mouse.Listener(on_click=on_click)
    mouse_listener.start()

    yolo_thread = threading.Thread(target=run_yolo_watcher, daemon=True)
    yolo_thread.start()

    # Keyboard listener runs in a thread (pynput supports this)
    kb_listener = keyboard.Listener(on_press=process_key_press)
    kb_listener.start()

    # OpenCV display loop MUST run on main thread (macOS requirement)
    try:
        run_display_loop()
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
