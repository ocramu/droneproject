from pynput import keyboard
from pynput.mouse import Controller as MouseController, Button
import time
import threading

mouse = MouseController()

# python3 '/Users/dyv/Desktop/droneproject/Neo 2/TakeOff&Forward2.py'

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

# --- Automation Flags ---
auto_sequence_running = False
killswitch_triggered = False
waiting_for_start = True
dist_input = 2.0

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

def check_sleep(duration):
    """Sleeps in small increments. Returns False if killswitch is hit, True otherwise."""
    global killswitch_triggered
    start_time = time.time()
    while time.time() - start_time < duration:
        if killswitch_triggered:
            return False
        time.sleep(0.05)
    return True

def automated_sequence(duration_seconds):
    """Handles the automated pre-takeoff, takeoff, and forward movement."""
    global auto_sequence_running, killswitch_triggered
    auto_sequence_running = True
    
    try:
        print("\n--- [AUTO] Sequence Starting ---")
        
        # 1. Pre-Takeoff
        print("[AUTO] Tapping Pre-Takeoff...")
        mouse.position = BTN_PRE_TAKEOFF
        time.sleep(0.05)
        mouse.click(Button.left)
        if not check_sleep(1.5): return # Wait for prompt to appear
        
        # 2. Takeoff (Jiggle included to bypass stationary hold filtering)
        print("[AUTO] Pressing and Holding Large Takeoff...")
        mouse.position = BTN_LARGE_TAKEOFF
        time.sleep(0.05)
        mouse.press(Button.left)
        
        start_hold = time.time()
        jiggle = 1
        hold_successful = True
        
        while time.time() - start_hold < 2.5: # Hold for 2.5 seconds
            if killswitch_triggered:
                hold_successful = False
                break
            
            # Micro-jiggle by 1 pixel to force OS to register continuous touch
            mouse.position = (BTN_LARGE_TAKEOFF[0] + jiggle, BTN_LARGE_TAKEOFF[1])
            jiggle *= -1 # Alternate between +1 and -1 pixel
            time.sleep(0.05)
            
        mouse.release(Button.left)
        if not hold_successful: return
        
        print("[AUTO] Waiting for drone to stabilize...")
        if not check_sleep(4.0): return
        
        # 3. Move Forward
        print(f"[AUTO] Moving forward for {duration_seconds} seconds...")
        perform_drag(R_JOY, (R_JOY[0], R_JOY[1] - DRAG_DIST))
        if not check_sleep(duration_seconds):
            mouse.release(Button.left)
            return
        mouse.release(Button.left)
        
        print("\n--- [AUTO] Sequence Complete. Manual keybinds active. ---")
        
    finally:
        # Always ensure flags are reset and mouse isn't stuck holding a click
        auto_sequence_running = False
        if killswitch_triggered:
            print("\n--- [KILLSWITCH] Sequence Aborted. Manual keybinds active. ---")

def process_key_press(key):
    global killswitch_triggered, waiting_for_start, auto_sequence_running, dist_input
    
    try:
        if hasattr(key, 'char') and key.char:
            k = key.char.lower()
        else:
            k = key.name

        # --- START TRIGGER ---
        if k == '1' and waiting_for_start:
            waiting_for_start = False
            print("\n[Action] '1' pressed. Starting automated sequence...")
            auto_thread = threading.Thread(target=automated_sequence, args=(dist_input,), daemon=True)
            auto_thread.start()
            return

        # --- KILLSWITCH CHECK ---
        if k == 'space':
            if auto_sequence_running:
                killswitch_triggered = True
                mouse.release(Button.left) # Emergency drop of any screen holds
            return

        # Ignore all manual input (except space/esc) if waiting for start or running auto
        if waiting_for_start or auto_sequence_running:
            return

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

        # Only process releases if manual controls are active
        if not auto_sequence_running and not waiting_for_start:
            if k in ['u', 'k', 'w', 'a', 's', 'd', 'up', 'down', 'left', 'right']:
                mouse.release(Button.left)
                print(f"[Action] Released {k}")

    except Exception as e:
        print(f"Error on release: {e}")

if __name__ == "__main__":
    # 1. Request distance (translates to time) before starting
    try:
        dist_input = float(input("Enter distance to move forward (in seconds of forward flight): "))
    except ValueError:
        print("Invalid input. Defaulting to 2.0 seconds.")
        dist_input = 2.0

    print("\n--- Drone Key Controller Ready ---")
    print("1. Switch to your mirror window so it is active.")
    print("2. Press '1' on your keyboard to begin the automated sequence.")
    print("------------------------------------------------------------")
    print("Press 'Spacebar' AT ANY TIME to kill the automated sequence.")
    print("Press 'Esc' to quit the program completely.\n")
    
    # 2. Start the keyboard listener and block the main thread
    with keyboard.Listener(on_press=process_key_press, on_release=process_key_release) as listener:
        listener.join()
