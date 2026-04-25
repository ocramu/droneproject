import wda
from pynput import keyboard
import time

# --- Configuration ---
# The IP address of your iPhone running WebDriverAgent
DEVICE_URL = 'http://192.168.1.XXX:8100'

# iPhone 15 Pro Max Logical Coordinates (Approximate based on your screenshots)
# You may need to tweak these slightly to hit the exact center of your UI
TAKEOFF_X, TAKEOFF_Y = 215, 650
L_JOY_X, L_JOY_Y = 120, 650
R_JOY_X, R_JOY_Y = 310, 650
DRAG_DIST = 40  # How far (in pixels) to drag the joystick from center

# Initialize the WDA Client
try:
    c = wda.Client(DEVICE_URL)
except Exception as e:
    print(f"Could not connect to iPhone. Is WDA running at {DEVICE_URL}?")
    exit()

# State Machine: "WAITING_TAKEOFF" -> "FLYING"
state = "WAITING_TAKEOFF"

def process_controls(key):
    global state
    
    # -----------------------------------------
    # STATE 1: Waiting for Takeoff
    # -----------------------------------------
    if state == "WAITING_TAKEOFF":
        if hasattr(key, 'char') and key.char == 'y':
            print("\n[Action] Initiating Takeoff...")
            # Tap and hold the takeoff button for 3 seconds
            c.tap_hold(TAKEOFF_X, TAKEOFF_Y, 3.0)
            
            state = "FLYING"
            print(">>> STATUS: FLYING. Joysticks active. Press 'h' to land. <<<")

    # -----------------------------------------
    # STATE 2: Flying (Listening to Joysticks)
    # -----------------------------------------
    elif state == "FLYING":
        # -- Landing ('h' key) --
        if hasattr(key, 'char') and key.char == 'h':
            print("\n[Action] Initiating Landing...")
            c.tap_hold(TAKEOFF_X, TAKEOFF_Y, 3.0) # Assuming 'h' uses the same button
            state = "WAITING_TAKEOFF"
            print(">>> STATUS: LANDED. Press 'y' to take off. <<<")
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


def on_press(key):
    try:
        process_controls(key)
    except Exception as e:
        print(f"Error processing key: {e}")

def on_release(key):
    # Press ESC to stop the program safely
    if key == keyboard.Key.esc:
        print("Exiting flight control...")
        return False 

print("--- Drone Flight Control Online ---")
print(f"Current State: {state}. Press 'y' to start.")
print("Press 'esc' to quit entirely.")

# Start listening to the keyboard
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
