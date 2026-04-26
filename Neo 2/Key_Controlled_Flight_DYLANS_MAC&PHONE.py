from pynput import keyboard
from pynput.mouse import Controller as MouseController, Button
import time

mouse = MouseController()

# --- Screen Coordinate Configuration ---
BTN_PRE_TAKEOFF = (507, 447)   
BTN_LARGE_TAKEOFF = (856, 534) 
BTN_PRE_LAND = (507, 447)      
BTN_LARGE_LAND = (856, 534)    

# Joysticks
L_JOY = (601, 693)  
R_JOY = (1106, 695) 
DRAG_DIST = 60      

active_keys = set()

def perform_drag(start_pos, target_pos):
    """Simulates a human dragging a finger on a screen across multiple small steps."""
    # 1. Snap to joystick center
    mouse.position = start_pos
    time.sleep(0.02)
    
    # 2. Touch the screen
    mouse.press(Button.left)
    time.sleep(0.05) # Crucial wait for iOS to register the touch
    
    # 3. Micro-step to the edge (forces macOS to register a continuous drag)
    steps = 10
    dx = (target_pos[0] - start_pos[0]) / steps
    dy = (target_pos[1] - start_pos[1]) / steps
    
    for i in range(1, steps + 1):
        mouse.position = (start_pos[0] + int(dx * i), start_pos[1] + int(dy * i))
        time.sleep(0.01)

def process_key_press(key):
    try:
        if hasattr(key, 'char') and key.char:
            k = key.char.lower()
        else:
            k = key.name

        if k in active_keys:
            return  
        active_keys.add(k)

        # ---------------- TAKE OFF / LANDING ----------------
        if k == 'y':
            print("[Action] Tapping Pre-Takeoff...")
            mouse.position = BTN_PRE_TAKEOFF
            mouse.click(Button.left)
            
        elif k == 'u':
            print("[Action] Pressing and Holding Large Takeoff...")
            mouse.position = BTN_LARGE_TAKEOFF
            time.sleep(0.02)
            mouse.press(Button.left)

        elif k == 'l':
            print("[Action] Tapping Pre-Land...")
            mouse.position = BTN_PRE_LAND
            mouse.click(Button.left)
            
        elif k == 'k':
            print("[Action] Pressing and Holding Large Land...")
            mouse.position = BTN_LARGE_LAND
            time.sleep(0.02)
            mouse.press(Button.left)

        # ---------------- LEFT JOYSTICK ----------------
        elif k in ['w', 'a', 's', 'd']:
            print(f"[Action] Left Joystick Dragging for '{k}'...")
            if k == 'w':   # Up
                perform_drag(L_JOY, (L_JOY[0], L_JOY[1] - DRAG_DIST))
            elif k == 's': # Down
                perform_drag(L_JOY, (L_JOY[0], L_JOY[1] + DRAG_DIST))
            elif k == 'a': # Turn Left
                perform_drag(L_JOY, (L_JOY[0] - DRAG_DIST, L_JOY[1]))
            elif k == 'd': # Turn Right
                perform_drag(L_JOY, (L_JOY[0] + DRAG_DIST, L_JOY[1]))

        # ---------------- RIGHT JOYSTICK ----------------
        elif k in ['up', 'down', 'left', 'right']:
            print(f"[Action] Right Joystick Dragging for '{k}'...")
            if k == 'up':    # Forward
                perform_drag(R_JOY, (R_JOY[0], R_JOY[1] - DRAG_DIST))
            elif k == 'down':  # Backward
                perform_drag(R_JOY, (R_JOY[0], R_JOY[1] + DRAG_DIST))
            elif k == 'left':  # Move Left
                perform_drag(R_JOY, (R_JOY[0] - DRAG_DIST, R_JOY[1]))
            elif k == 'right': # Move Right
                perform_drag(R_JOY, (R_JOY[0] + DRAG_DIST, R_JOY[1]))

    except Exception as e:
        print(f"Error on press: {e}")

def process_key_release(key):
    try:
        if hasattr(key, 'char') and key.char:
            k = key.char.lower()
        else:
            k = key.name

        if k in active_keys:
            active_keys.remove(k)

        # Release logic: Let go of mouse clicks
        if k in ['u', 'k', 'w', 'a', 's', 'd', 'up', 'down', 'left', 'right']:
            mouse.release(Button.left)
            print(f"[Action] Released {k}")

    except Exception as e:
        print(f"Error on release: {e}")

if __name__ == "__main__":
    print("--- Drone Key Controller Started ---")
    print("Press 'Esc' to quit the program.")
    
    with keyboard.Listener(on_press=process_key_press, on_release=process_key_release) as listener:
        listener.join()
