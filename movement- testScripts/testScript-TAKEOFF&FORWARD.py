import time
import Quartz
import threading
from pynput import keyboard

# Speed Calibration
FT_PER_SEC_ASCEND = 6.5   
FT_PER_SEC_FORWARD = 8.0  

# Coordinates (Verify these in BlueStacks!)
L_JOY_CENTER = (200, 400)
L_UP = (200, 300)
R_JOY_CENTER = (1000, 400)
R_UP = (1000, 300)
BTN_TAKEOFF = (640, 450)

running = True # Global flag to stop the drone

def send_mouse(x, y, event):
    if not running: return
    q_event = Quartz.CGEventCreateMouseEvent(None, event, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, q_event)

def hold_direction(center, target, duration):
    if not running: return
    send_mouse(center[0], center[1], Quartz.kCGEventLeftMouseDown)
    send_mouse(target[0], target[1], Quartz.kCGEventLeftMouseDragged)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        if not running: break
        time.sleep(0.1)
        
    send_mouse(target[0], target[1], Quartz.kCGEventLeftMouseUp)

def on_press(key):
    global running
    if key == keyboard.Key.space: # KILL SWITCH
        print("\n!!! EMERGENCY STOP TRIGGERED !!!")
        running = False
        return False 

def main_mission():
    global running
    print("Mission starts in 5s. Focus BlueStacks!")
    time.sleep(5)

    print("Taking off...")
    send_mouse(BTN_TAKEOFF[0], BTN_TAKEOFF[1], Quartz.kCGEventLeftMouseDown)
    send_mouse(BTN_TAKEOFF[0], BTN_TAKEOFF[1], Quartz.kCGEventLeftMouseUp)
    time.sleep(4)

    print("Ascending 30ft...")
    hold_direction(L_JOY_CENTER, L_UP, 30 / FT_PER_SEC_ASCEND)
    
    while running:
        dist_input = input("Distance forward (feet) or 'q' to quit: ")
        if dist_input.lower() == 'q': break
        try:
            dist = float(dist_input)
            hold_direction(R_JOY_CENTER, R_UP, dist / FT_PER_SEC_FORWARD)
        except ValueError:
            print("Invalid number.")

if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    main_mission()
    running = False
    listener.stop()
