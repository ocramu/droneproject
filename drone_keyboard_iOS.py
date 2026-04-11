from ppadb.client import Client as AdbClient
import time

# Setup ADB connection
client = AdbClient(host="127.0.0.1", port=5037)
devices = client.devices()

if len(devices) == 0:
    print("No device attached")
    quit()

device = devices[0]

# Mapping coordinates (Replace these with your specific screen coordinates)
# Format: (x, y)
CONTROLS = {
    'takeoff': (200, 500),
    'land': (200, 700),
    'forward': (850, 400),
    'backward': (850, 600),
    'left': (750, 500),
    'right': (950, 500)
}

def send_command(command, duration=0.1):
    x, y = CONTROLS[command]
    # 'input swipe' can be used to simulate a long press (holding the stick)
    device.shell(f"input swipe {x} {y} {x} {y} {int(duration * 1000)}")

# Example Keybinding Loop
import keyboard # pip install keyboard

print("Controls: T=Takeoff, L=Land, Arrow Keys=Move. Press ESC to stop.")

while True:
    if keyboard.is_pressed('t'):
        send_command('takeoff')
    elif keyboard.is_pressed('l'):
        send_command('land')
    elif keyboard.is_pressed('up'):
        send_command('forward')
    # Add more keybinds here...
    
    if keyboard.is_pressed('esc'):
        break
    time.sleep(0.05)
