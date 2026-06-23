import socket
import time

HOST = '127.0.0.1'
PORT = 50007

def send(sock, msg):
    sock.sendall((msg + "\n").encode())

def key_down(sock, key):
    # key like "w", "a", "s", "d", "Up", "Left", "Down", "Right"
    send(sock, f"key_down:{key}")

def key_up(sock, key):
    send(sock, f"key_up:{key}")

if __name__ == "__main__":
    with socket.create_connection((HOST, PORT)) as s:
        print("Connected to joystick server")

        # demo: press W, then Up, then release both
        key_down(s, "w")
        time.sleep(0.5)
        key_down(s, "Up")
        time.sleep(0.5)
        key_up(s, "w")
        time.sleep(0.5)
        key_up(s, "Up")

        # keep program open a bit so you can see the effect
        time.sleep(1.0)
