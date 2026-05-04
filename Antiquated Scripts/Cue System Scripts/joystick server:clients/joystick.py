import tkinter as tk

KEY_MAP = {
    'w': ('left', 'up'),
    'a': ('left', 'left'),
    's': ('left', 'down'),
    'd': ('left', 'right'),
    'Up': ('right', 'up'),
    'Left': ('right', 'left'),
    'Down': ('right', 'down'),
    'Right': ('right', 'right'),
}

class JoystickApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Joystick example")
        self.resizable(False, False)

        self.canvas = tk.Canvas(self, width=360, height=220, bg="#f0f0f0")
        self.canvas.pack(padx=10, pady=10)

        self.left_center = (90, 110)
        self.right_center = (270, 110)
        self.size = 30

        self.left_arrows = self._create_joystick(self.left_center)
        self.right_arrows = self._create_joystick(self.right_center)

        self.key_to_item = {
            'w': self.left_arrows['up'],
            'a': self.left_arrows['left'],
            's': self.left_arrows['down'],
            'd': self.left_arrows['right'],
            'Up': self.right_arrows['up'],
            'Left': self.right_arrows['left'],
            'Down': self.right_arrows['down'],
            'Right': self.right_arrows['right'],
        }

        # hidden entry to reliably grab keys
        self.grabber = tk.Entry(self, width=1)
        self.grabber.place(x=-200, y=-200)
        self.grabber.focus_set()

        self.pressed = set()
        self.grabber.bind('<KeyPress>', self.on_key_press)
        self.grabber.bind('<KeyRelease>', self.on_key_release)
        self.bind_all('<Button-1>', lambda e: self.grabber.focus_set())

    def _create_joystick(self, center):
        cx, cy = center
        s = self.size
        gap = 10
        arrows = {}

        # up triangle
        arrows['up'] = self.canvas.create_polygon(
            cx - s//2, cy - gap - s//2,
            cx + s//2, cy - gap - s//2,
            cx,        cy - gap - s,
            fill='black', outline='black'
        )
        # down triangle
        arrows['down'] = self.canvas.create_polygon(
            cx - s//2, cy + gap + s//2,
            cx + s//2, cy + gap + s//2,
            cx,        cy + gap + s,
            fill='black', outline='black'
        )
        # left triangle
        arrows['left'] = self.canvas.create_polygon(
            cx - gap - s,   cy,
            cx - gap - s//2, cy - s//2,
            cx - gap - s//2, cy + s//2,
            fill='black', outline='black'
        )
        # right triangle
        arrows['right'] = self.canvas.create_polygon(
            cx + gap + s,    cy,
            cx + gap + s//2, cy - s//2,
            cx + gap + s//2, cy + s//2,
            fill='black', outline='black'
        )
        return arrows

    def _norm(self, keysym):
        return keysym if len(keysym) > 1 else keysym.lower()

    def on_key_press(self, event):
        key = self._norm(event.keysym)
        print("PRESS:", key)  # debug
        if key in self.key_to_item and key not in self.pressed:
            item = self.key_to_item[key]
            self.canvas.itemconfig(item, fill='green', outline='green')
            self.pressed.add(key)

    def on_key_release(self, event):
        key = self._norm(event.keysym)
        print("RELEASE:", key)  # debug
        if key in self.key_to_item and key in self.pressed:
            item = self.key_to_item[key]
            self.canvas.itemconfig(item, fill='black', outline='black')
            self.pressed.remove(key)

if __name__ == '__main__':
    JoystickApp().mainloop()
