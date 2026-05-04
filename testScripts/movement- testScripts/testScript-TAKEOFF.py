import time
import Quartz
from pynput import keyboard

# --- CONFIGURATION (Adjust for your screen resolution) ---
# Left Joystick (Throttle/Yaw)
L_JOY_CENTER = (200, 400)
L_UP = (200, 300)    # W: Ascend
L_DOWN = (200, 500)  # S: Descend
L_LEFT = (100, 400)  # A: Yaw Left
L_RIGHT = (300, 400) # D: Yaw Right

# Right Joystick (Pitch/Roll)
R_JOY_CENTER = (1000, 400)
R_UP = (1000, 300)   # I: Pitch Forward
R_DOWN = (1000, 500) # K: Pitch Backward
R_LEFT = (900, 400)  # J: Roll Left
R_RIGHT = (1100, 400)# L: Roll Right

def send_mouse(x, y, event):
    quartz_event = Quartz.CGEventCreateMouseEvent(None, event, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, quartz_event)

def move_joystick(center, target):
    # Drag from center to target to simulate movement
    send_mouse(center[0], center[1], Quartz.kCGEventLeftMouseDown)
    send_mouse(target[0], target[1], Quartz.kCGEventLeftMouseDragged)
    # Note: We keep it held down until the key is released

def reset_joystick(center):
    send_mouse(center[0], center[1], Quartz.kCGEventLeftMouseUp)

def on_press(key):
    try:
        if key.char == 'w': move_joystick(L_JOY_CENTER, L_UP)
        elif key.char == 's': move_joystick(L_JOY_CENTER, L_DOWN)
        elif key.char == 'a': move_joystick(L_JOY_CENTER, L_LEFT)
        elif key.char == 'd': move_joystick(L_JOY_CENTER, L_RIGHT)
        
        # Pitch/Roll mapping (using IJKL to avoid WASD conflict)
        elif key.char == 'i': move_joystick(R_JOY_CENTER, R_UP)
        elif key.char == 'k': move_joystick(R_JOY_CENTER, R_DOWN)
        elif key.char == 'j': move_joystick(R_JOY_CENTER, R_LEFT)
        elif key.char == 'l': move_joystick(R_JOY_CENTER, R_RIGHT)
        
        # Emergency Land
        elif key.char == 'q': print("Emergency Land Triggered") 
    except AttributeError:
        pass

def on_release(key):
    # When you let go, the "joystick" returns to center
    if hasattr(key, 'char') and key.char in ['w', 's', 'a', 'd']:
        reset_joystick(L_JOY_CENTER)
    if hasattr(key, 'char') and key.char in ['i', 'k', 'j', 'l']:
        reset_joystick(R_JOY_CENTER)
    if key == keyboard.Key.esc:
        return False # Stop listener

# Start the keyboard listener in a separate thread
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("Control System Active. Use W/S/A/D and I/J/K/L. Press ESC to quit.")
listener.join()
