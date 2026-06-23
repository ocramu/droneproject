import socket

HOST = '127.0.0.1'
PORT = 50008

def main():
    print("Connecting to joystick sequence server...")
    with socket.create_connection((HOST, PORT)) as s:
        print("Connected. Enter sequences of letters like 'rlrrud'.")
        print("r=right, l=left, u=up, d=down; empty line to quit.")
        while True:
            seq = input("Sequence> ").strip()
            if not seq:
                break
            # just send the raw string plus newline
            s.sendall((seq + "\n").encode())

if __name__ == "__main__":
    main()
