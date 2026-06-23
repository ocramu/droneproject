import tkinter as tk
import socket
import threading

HOST = '127.0.0.1'
PORT = 50008      # same as before
STEP_MS = 2000    # 2 seconds per arrow

class JoystickSeqApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("8-way Joystick sequence server")
        self.resizable(False, False)

        self.canvas = tk.Canvas(self, width=360, height=260, bg="#f0f0f0")
        self.canvas.pack(padx=10, pady=10)

        self.size = 30
        self.left_center = (90, 130)   # slightly lower to fit diagonals
        self.right_center = (270, 130)

        self.left_arrows = self._create_joystick(self.left_center)
        self.right_arrows = self._create_joystick(self.right_center)

        # map direction letter -> left joystick arrow (8-way)
        # u,d,l,r are cardinal; q,e,z,c are diagonals
        self.dir_to_item = {
            'u': self.left_arrows['up'],
            'd': self.left_arrows['down'],
            'l': self.left_arrows['left'],
            'r': self.left_arrows['right'],
            'q': self.left_arrows['up_left'],
            'e': self.left_arrows['up_right'],
            'z': self.left_arrows['down_left'],
            'c': self.left_arrows['down_right'],
        }

        # sequence playback state
        self.current_sequence = ""
        self.current_index = -1
        self.current_item = None

        # start socket thread
        threading.Thread(target=self.socket_thread, daemon=True).start()

    def _create_joystick(self, center):
        cx, cy = center
        s = self.size
        gap = 10
        diag_offset = int(s * 0.7)
        arrows = {}

        # Cardinal directions (same as before)
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

        # Diagonals: simple triangles at 45° around the center

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

    # --- sequence playback ---

    def start_sequence(self, seq: str):
        """Called when a new sequence string (e.g. 'rlrrudqezc') arrives."""
        # cancel any current highlight
        if self.current_item is not None:
            self.canvas.itemconfig(self.current_item, fill='black', outline='black')
            self.current_item = None

        self.current_sequence = seq.lower()
        self.current_index = -1

        # kick off playback
        self.after(0, self._step_sequence)

    def _step_sequence(self):
        # turn off previous item, if any
        if self.current_item is not None:
            self.canvas.itemconfig(self.current_item, fill='black', outline='black')
            self.current_item = None

        self.current_index += 1
        if self.current_index >= len(self.current_sequence):
            # finished
            return

        ch = self.current_sequence[self.current_index]
        item = self.dir_to_item.get(ch)
        if item is not None:
            # turn this arrow green
            self.canvas.itemconfig(item, fill='green', outline='green')
            self.current_item = item

        # schedule next step after 2 seconds
        self.after(STEP_MS, self._step_sequence)

    # --- socket handling ---

    def socket_thread(self):
        """Listen for clients and accept lines like 'rlrrudqezc\\n'."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)
            print(f"Sequence server listening on {HOST}:{PORT}")
            while True:
                conn, addr = s.accept()
                print("Client connected:", addr)
                threading.Thread(target=self.handle_client,
                                 args=(conn, addr),
                                 daemon=True).start()

    def handle_client(self, conn, addr):
        with conn:
            buf = b""
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    seq = line.decode().strip()
                    if not seq:
                        continue
                    print(f"Got sequence from {addr}: {seq}")
                    # schedule playback on main Tk thread
                    self.after(0, self.start_sequence, seq)

if __name__ == "__main__":
    app = JoystickSeqApp()
    app.mainloop()
