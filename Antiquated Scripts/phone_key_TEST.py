import subprocess
from pynput import keyboard
import time

# --- CONFIGURATION ---
X_COORD = 500
Y_COORD = 1200
# ---------------------

def send_tap(x, y):
    """Sends a tap command to the connected Android device via ADB."""
    cmd = f"adb shell input tap {x} {y}"
    try:
        # Using check=False so the script doesn't crash if ADB isn't ready
        subprocess.run(cmd, shell=True)
        print(f"Tap sent to ({x}, {y})")
    except Exception as e:
        print(f"Error sending tap: {e}")

def on_press(key):
    try:
        # Check if the alphanumeric key 's' is pressed
        if key.char == 's':
            send_tap(X_COORD, Y_COORD)
    except AttributeError:
        # This handles special keys like 'esc'
        if key == keyboard.Key.esc:
            print("Exiting...")
            return False  # Stops the listener

print(f"Script active. Press 's' to tap at ({X_COORD}, {Y_COORD}).")
print("Press 'esc' to stop.")

# This starts the listener and keeps it running
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
