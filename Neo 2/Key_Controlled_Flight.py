import wda
from pynput import keyboard
import time

# --- Configuration ---
# The IP address of your iPhone running WebDriverAgent
DEVICE_URL = 'http://192.168.1.XXX:8100'

# iPhone 15 Pro Max Logical Coordinates (Landscape max: 932x430)
# These are estimates based on standard UI layouts. You will need to fine-tune 
# these based on your phone's specific logical coordinate grid.
SMALL_BTN_X, SMALL_BTN_Y = 80, 215       # The small takeoff/land button on the left edge
LARGE_BTN_X, LARGE_BTN_Y = 466, 215      # The large center takeoff/land confirmation button
L_JOY_X, L_JOY_Y = 180, 300              # Center of the Left Joystick
R_JOY_X, R_JOY_Y = 752, 300              # Center of the Right Joystick

DRAG_DIST = 40  # How far (in logical pixels) to swipe the joystick from center

# Initialize the WDA Client
try:
    c = wda.Client(DEVICE_URL)
except Exception as e:
    print(f"Could not connect to iPhone. Is WDA running at {DEVICE_URL}?")
    exit()

# State Machine: Tracks the current phase of the flight
state = "GROUNDED"
active_keys = set() # Prevents spamming actions when a key is held down

def process_controls(key):
    global state
    
    # -----------------------------------------
    # STATE 1: Grounded (Ready for pre-takeoff)
    # -----------------------------------------
    if state == "GROUNDED":
        if hasattr(key, 'char') and key.char == 'y':
            print("\n[Action] Tapping small Takeoff button...")
            c.tap(SMALL_BTN_X, SMALL_BTN_Y)
            state = "PRE_TAKEOFF"
            print(">>> STATUS: PRE-TAKEOFF. Press 'u' to confirm and hold takeoff. <<<")

    # -----------------------------------------
    # STATE 2: Pre-Takeoff (Waiting for confirmation)
    # -----------------------------------------
    elif state == "PRE_TAKEOFF":
        if hasattr(key, 'char') and key.char == 'u':
            print("\n[Action] Holding large Takeoff button...")
            c.tap_hold(LARGE_BTN_X, LARGE_BTN_Y, 3.0)
            state = "FLYING"
            print(">>> STATUS: FLYING. Joysticks active. Press 'l' to initiate landing. <<<")

    # -----------------------------------------
    # STATE 3: Flying (Listening to Joysticks)
    # -----------------------------------------
    elif state == "FLYING":
        # -- Initiate Landing ('L' key) --
        if hasattr(key, 'char') and key.char == 'l':
            print("\n[Action] Tapping small Landing button...")
            c.tap(SMALL_BTN_X, SMALL_BTN_Y)
            state = "PRE_LANDING"
            print(">>> STATUS: PRE-LANDING. Press 'k' to confirm and hold landing. <<<")
            return

        # -- Left Joystick (W, A, S, D) --
        if hasattr(key, 'char'):
            char = key.char.lower()
            if char == 'w':
                c.swipe(L_JOY_X, L_JOY_Y, L_JOY_X, L_JOY_Y - DRAG_DIST, 0.5)
            elif char == 's':
                c.swipe(L_JOY_X, L_JOY_Y, L_JOY_X, L_JOY_Y + DRAG_DIST, 0.5)
            elif char == 'a':
                c.swipe(L_JOY_X, L_JOY_Y, L_JOY_X - DRAG_DIST, L_JOY_Y, 0.5)
            elif char == 'd':
                c.swipe(L_JOY_X, L_JOY_Y, L_JOY_X + DRAG_DIST, L_JOY_Y, 0.5)

        # -- Right Joystick (Arrow Keys) --
        elif key == keyboard.Key.up:
            c.swipe(R_JOY_X, R_JOY_Y, R_JOY_X, R_JOY_Y - DRAG_DIST, 0.5)
        elif key == keyboard.Key.down:
            c.swipe(R_JOY_X, R_JOY_Y, R_JOY_X, R_JOY_Y + DRAG_DIST, 0.5)
        elif key == keyboard.Key.left:
            c.swipe(R_JOY_X, R_JOY_Y, R_JOY_X - DRAG_DIST, R_JOY_Y, 0.5)
        elif key == keyboard.Key.right:
            c.swipe(R_JOY_X, R_JOY_Y, R_JOY_X + DRAG_DIST, R_JOY_Y, 0.5)

    # -----------------------------------------
    # STATE 4: Pre-Landing (Waiting for confirmation)
    # -----------------------------------------
    elif state == "PRE_LANDING":
        if hasattr(key, 'char') and key.char == 'k':
            print("\n[Action] Holding large Landing button...")
            c.tap_hold(LARGE_BTN_X, LARGE_BTN_Y, 3.0)
            state = "GROUNDED"
            print(">>> STATUS: GROUNDED. Press 'y' to open takeoff menu. <<<")

# ==========================================
# KEYBOARD LISTENERS
# ==========================================
def on_press(key):
    # Debounce logic to prevent holding a key from triggering WDA commands 30 times a second
    k = getattr(key, 'char', key)
    if k in active_keys:
        return
    active_keys.add(k)
    
    try:
        process_controls(key)
    except Exception as e:
        print(f"Error processing key: {e}")

def on_release(key):
    k = getattr(key, 'char', key)
    if k in active_keys:
        active_keys.remove(k)
        
    # Press ESC to stop the program safely
    if key == keyboard.Key.esc:
        print("Exiting flight control...")
        return False 

# ==========================================
# EXECUTION
# ==========================================
print("--- Drone Flight Control Online ---")
print(f"Current State: {state}. Press 'y' to start.")
print("Press 'esc' to quit entirely.")

# Start listening to the keyboard
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
