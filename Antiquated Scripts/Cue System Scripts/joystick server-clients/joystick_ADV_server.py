import tkinter as tk
import socket
import threading

HOST = '127.0.0.1'
PORT = 50007  # any free port

KEY_MAP = {
    'w': 'w',
    'a': 'a',
    's': 's',
    'd': 'd',
    'q': 'q',
    'e': 'e',
    'z': 'z',
    'c': 'c',
    'Up': 'Up',
    'Left': 'Left',
    'Down': 'Down',
    'Right': 'Right',
}

class JoystickApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("8-way Joystick example (server)")
        self.resizable(False, False)

        self.canvas = tk.Canvas(self, width=360, height=260, bg="#f0f0f0")
        self.canvas.pack(padx=10, pady=10)

        self.left_center = (90, 130)   # a bit lower to fit diagonals
        self.right_center = (270, 130)
        self.size = 30

        self.left_arrows = self._create_joystick(self.left_center)
        self.right_arrows = self._create_joystick(self.right_center, diagonals=False)

        # mapping from key -> canvas item
        self.key_to_item = {
            # left joystick cardinals
            'w': self.left_arrows['up'],
            'a': self.left_arrows['left'],
            's': self.left_arrows['down'],
            'd': self.left_arrows['right'],
            # left joystick diagonals
            'q': self.left_arrows['up_left'],
            'e': self.left_arrows['up_right'],
            'z': self.left_arrows['down_left'],
            'c': self.left_arrows['down_right'],
            # right joystick (4-way)
            'Up': self.right_arrows['up'],
            'Left': self.right_arrows['left'],
            'Down': self.right_arrows['down'],
            'Right': self.right_arrows['right'],
        }

        self.pressed = set()

        # optional: still allow local keyboard control
        grabber = tk.Entry(self, width=1)
        grabber.place(x=-200, y=-200)
        grabber.focus_set()
        grabber.bind('<KeyPress>', self.on_tk_key_press)
        grabber.bind('<KeyRelease>', self.on_tk_key_release)
        self.bind_all('<Button-1>', lambda e: grabber.focus_set())

        # start network listener thread
        threading.Thread(target=self.socket_thread, daemon=True).start()

    def _create_joystick(self, center, diagonals=True):
        cx, cy = center
        s = self.size
        gap = 10
        diag_offset = int(s * 0.7)
        arrows = {}

        # 4 cardinal directions
        arrows['up'] = self.canvas.create_polygon(
            cx - s//2, cy - gap - s//2,
            cx + s//2, cy - gap - s//2,
            cx,        cy - gap - s,
            fill='black', outline='black'
        )
        arrows['down'] = self.canvas.create_polygon(
            cx - s//2, cy + gap + s//2,
            cx + s//2, cy + gap + s//2,
            cx,        cy + gap + s,
            fill='black', outline='black'
        )
        arrows['left'] = self.canvas.create_polygon(
            cx - gap - s,    cy,
            cx - gap - s//2, cy - s//2,
            cx - gap - s//2, cy + s//2,
            fill='black', outline='black'
        )
        arrows['right'] = self.canvas.create_polygon(
            cx + gap + s,    cy,
            cx + gap + s//2, cy - s//2,
            cx + gap + s//2, cy + s//2,
            fill='black', outline='black'
        )

        if diagonals:
            # up-left (q)
            arrows['up_left'] = self.canvas.create_polygon(
                cx - diag_offset,     cy - diag_offset//2,
                cx - diag_offset//2,  cy - diag_offset,
                cx - diag_offset//2,  cy - diag_offset//4,
                fill='black', outline='black'
            )
            # up-right (e)
            arrows['up_right'] = self.canvas.create_polygon(
                cx + diag_offset,     cy - diag_offset//2,
                cx + diag_offset//2,  cy - diag_offset,
                cx + diag_offset//2,  cy - diag_offset//4,
                fill='black', outline='black'
            )
            # down-left (z)
            arrows['down_left'] = self.canvas.create_polygon(
                cx - diag_offset,     cy + diag_offset//2,
                cx - diag_offset//2,  cy + diag_offset,
                cx - diag_offset//2,  cy + diag_offset//4,
                fill='black', outline='black'
            )
            # down-right (c)
            arrows['down_right'] = self.canvas.create_polygon(
                cx + diag_offset,     cy + diag_offset//2,
                cx + diag_offset//2,  cy + diag_offset,
                cx + diag_offset//2,  cy + diag_offset//4,
                fill='black', outline='black'
            )
        return arrows

    def _norm(self, k):
        return k if len(k) > 1 else k.lower()

    # --- local keyboard (optional) ---
    def on_tk_key_press(self, event):
        self.handle_key(self._norm(event.keysym), "down")

    def on_tk_key_release(self, event):
        self.handle_key(self._norm(event.keysym), "up")

    # --- shared logic for key_down/key_up ---
    def handle_key(self, key, action):
        if key not in self.key_to_item:
            return

        if action == "down":
            if key in self.pressed:
                return
            item = self.key_to_item[key]
            self.canvas.itemconfig(item, fill='green', outline='green')
            self.pressed.add(key)
        elif action == "up":
            if key not in self.pressed:
                return
            item = self.key_to_item[key]
            self.canvas.itemconfig(item, fill='black', outline='black')
            self.pressed.remove(key)

    # --- socket listener ---
    def socket_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)
            print(f"Joystick server listening on {HOST}:{PORT}")
            conn, addr = s.accept()
            print("Client connected:", addr)
            with conn:
                buf = b""
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        msg = line.decode().strip()
                        # messages: "key_down:q", "key_up:Down", etc.
                        self.process_message(msg)

    def process_message(self, msg):
        # schedule on Tk main thread
        self.after(0, self._process_message_on_main, msg)

    def _process_message_on_main(self, msg):
        # expected formats: key_down:X, key_up:X
        if msg.startswith("key_down:"):
            key = msg[len("key_down:"):]
            self.handle_key(self._norm(key), "down")
        elif msg.startswith("key_up:"):
            key = msg[len("key_up:"):]
            self.handle_key(self._norm(key), "up")

if __name__ == '__main__':
    app = JoystickApp()
    app.mainloop()
