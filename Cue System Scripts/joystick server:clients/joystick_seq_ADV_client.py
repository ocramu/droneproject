import socket

HOST = '127.0.0.1'
PORT = 50008

def main():
    print("Connecting to joystick sequence server...")
    with socket.create_connection((HOST, PORT)) as s:
        print("Connected.")
        print("Enter sequences like 'rlrrudqezc'.")
        print("r=right, l=left, u=up, d=down, q=up-left, e=up-right, z=down-left, c=down-right")
        print("Empty line to quit.")
        while True:
            seq = input("Sequence> ").strip()
            if not seq:
                break
            # raw sequence string, one line
            s.sendall((seq + "\n").encode())

if __name__ == "__main__":
    main()
