import time
import Quartz
import threading
from pynput import keyboard

# --- CALIBRATION (Adjust these after your first test flight) ---
FT_PER_SEC_ASCEND = 6.5   
FT_PER_SEC_FORWARD = 8.0  

# --- COORDINATES (Use the helper script to find these) ---
L_JOY_CENTER = (200, 400)
L_UP = (200, 300)
R_JOY_CENTER = (1000, 400)
R_UP = (1000, 300)      # Forward
R_DOWN = (1000, 500)    # Backward (Brake)
BTN_TAKEOFF = (640, 450)

running = True 

def send_mouse(x, y, event):
    if not running: return
    q_event = Quartz.CGEventCreateMouseEvent(None, event, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, q_event)

def hold_direction(center, target, duration):
    if not running: return
    send_mouse(center[0], center[1], Quartz.kCGEventLeftMouseDown)
    send_mouse(target[0], target[1], Quartz.kCGEventLeftMouseDragged)
    time.sleep(duration)
    send_mouse(target[0], target[1], Quartz.kCGEventLeftMouseUp)

def apply_brake():
    """Briefly pulls back to stop coasting."""
    print("Applying active brake...")
    hold_direction(R_JOY_CENTER, R_DOWN, 0.3)

def on_press(key):
    global running
    if key == keyboard.Key.space:
        print("\n!!! EMERGENCY STOP !!!")
        running = False
        return False 

def main_mission():
    global running
    
    # --- STAGE 1: PRE-FLIGHT INPUT ---
    print("--- PRE-FLIGHT PLANNING ---")
    try:
        dist = float(input("Enter distance to move forward after 30ft ascent (feet): "))
    except ValueError:
        print("Invalid input. Please restart and enter a number.")
        return

    print(f"\nPlan confirmed: Takeoff -> 30ft Ascent -> {dist}ft Forward.")
    print("You have 5 seconds to switch to the BlueStacks window...")
    time.sleep(5)

    # --- STAGE 2: TAKEOFF ---
    print("Executing: Takeoff...")
    send_mouse(BTN_TAKEOFF[0], BTN_TAKEOFF[1], Quartz.kCGEventLeftMouseDown)
    send_mouse(BTN_TAKEOFF[0], BTN_TAKEOFF[1], Quartz.kCGEventLeftMouseUp)
    time.sleep(5) # Give it extra time to stabilize

    # --- STAGE 3: ASCEND ---
    if running:
        print("Executing: Ascending 30ft...")
        hold_direction(L_JOY_CENTER, L_UP, 30 / FT_PER_SEC_ASCEND)
        time.sleep(1) # Brief pause to settle

    # --- STAGE 4: MOVE FORWARD ---
    if running:
        print(f"Executing: Moving forward {dist}ft...")
        hold_direction(R_JOY_CENTER, R_UP, dist / FT_PER_SEC_FORWARD)
        apply_brake()

    print("\nMission Complete. Manual control (WASD/IJKL) is now active.")
    print("Press SPACE to kill the script or ESC to exit listener.")

if __name__ == "__main__":
    # Keyboard listener stays active for manual override at any time
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    main_mission()
    
    # Keep the script alive so you can fly manually after the mission
    listener.join()
