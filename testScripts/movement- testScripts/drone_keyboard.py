import time
import Quartz
from pynput import keyboard

#TO RUN DV MAC: python3 '/Users/dyv/Desktop/droneproject/movement- testScripts/drone_keyboard.py'


# Calibration
FT_PER_SEC_ASCEND = 6.5
FT_PER_SEC_FORWARD = 8.0

# Raw macOS virtual key codes
KEY_TAKEOFF = "t"
KEY_ASCEND = "w"
KEY_DESCEND = "s"
KEY_FORWARD = 126   # Up Arrow
KEY_BACKWARD = 125  # Down Arrow
KEY_LEFT = 123      # Left Arrow
KEY_RIGHT = 124     # Right Arrow
KEY_ROTATE_LEFT = "a"
KEY_ROTATE_RIGHT = "d"

running = True


def keycode_for_char(ch: str) -> int:
    mapping = {
        "a": 0,
        "s": 1,
        "d": 2,
        "f": 3,
        "h": 4,
        "g": 5,
        "z": 6,
        "x": 7,
        "c": 8,
        "v": 9,
        "b": 11,
        "q": 12,
        "w": 13,
        "e": 14,
        "r": 15,
        "y": 16,
        "t": 17,
        "1": 18,
        "2": 19,
        "3": 20,
        "4": 21,
        "6": 22,
        "5": 23,
        "=": 24,
        "9": 25,
        "7": 26,
        "-": 27,
        "8": 28,
        "0": 29,
        "]": 30,
        "o": 31,
        "u": 32,
        "[": 33,
        "i": 34,
        "p": 35,
        "l": 37,
        "j": 38,
        "'": 39,
        "k": 40,
        ";": 41,
        "\\": 42,
        ",": 43,
        "/": 44,
        "n": 45,
        "m": 46,
        ".": 47,
    }
    ch = ch.lower()
    if ch not in mapping:
        raise ValueError(f"Unsupported key character: {ch}")
    return mapping[ch]


def send_key_down(keycode: int):
    event = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def send_key_up(keycode: int):
    event = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def tap_key(key, hold_time=0.15):
    global running
    if not running:
        return

    keycode = keycode_for_char(key) if isinstance(key, str) else key
    send_key_down(keycode)
    time.sleep(hold_time)
    send_key_up(keycode)


def hold_key(key, duration):
    global running
    if not running:
        return

    keycode = keycode_for_char(key) if isinstance(key, str) else key
    send_key_down(keycode)
    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            if not running:
                break
            time.sleep(0.05)
    finally:
        send_key_up(keycode)


def on_press(key):
    global running
    if key == keyboard.Key.space:
        print("\n!!! EMERGENCY STOP TRIGGERED !!!")
        running = False
        return False


def main_mission():
    global running

    print("Mission starts in 5 seconds. Focus BlueStacks window now.")
    time.sleep(5)

    print("Sending takeoff key...")
    tap_key(KEY_TAKEOFF, hold_time=0.2)
    time.sleep(4)

    print("Ascending 30 ft...")
    hold_key(KEY_ASCEND, 30 / FT_PER_SEC_ASCEND)
    print("Ascend complete.")

    while running:
        dist_input = input("Distance forward (feet) or 'q' to quit: ").strip()
        if dist_input.lower() == "q":
            break

        try:
            dist = float(dist_input)
            duration = dist / FT_PER_SEC_FORWARD
            print(f"Moving forward {dist} ft for {duration:.2f} seconds...")
            hold_key(KEY_FORWARD, duration)
            print("Forward movement complete.")
        except ValueError:
            print("Invalid number.")


if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    try:
        main_mission()
    finally:
        running = False
        listener.stop()
