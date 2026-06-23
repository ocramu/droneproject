import tkinter as tk
import sys

def on_press(e):
    print("PRESS", e.keysym, "char:", repr(e.char), "focus:", root.focus_get(), file=sys.stdout, flush=True)

def on_release(e):
    print("RELEASE", e.keysym, "char:", repr(e.char), "focus:", root.focus_get(), file=sys.stdout, flush=True)

root = tk.Tk()
root.title("Key debug")
root.geometry("420x140")

tk.Label(root, text="Click this window, then press keys. Check Terminal for printed events.").pack(pady=8)
info = tk.Label(root, text="Focus owner: ")
info.pack(pady=4)

# show focus owner periodically
def show_focus():
    owner = root.focus_get()
    info.config(text=f"Focus owner: {owner}")
    root.after(250, show_focus)
show_focus()

# try multiple bindings: root, all, and a focused entry
root.bind('<KeyPress>', on_press)
root.bind('<KeyRelease>', on_release)
root.bind_all('<KeyPress>', on_press)
root.bind_all('<KeyRelease>', on_release)

entry = tk.Entry(root, width=1)
entry.place(x=-200, y=-200)
entry.focus_set()

entry.bind('<KeyPress>', on_press)
entry.bind('<KeyRelease>', on_release)

# attempt to force focus when window becomes active
def focus_force(e=None):
    try:
        entry.focus_set()
    except Exception:
        pass
root.bind('<Visibility>', focus_force)
root.bind('<FocusIn>', focus_force)

print("Started. Click the window, then press keys. If nothing prints, report OS version and keyboard type.", flush=True)
root.mainloop()
