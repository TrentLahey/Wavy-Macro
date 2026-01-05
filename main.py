import time
import threading
from pynput import keyboard, mouse

kb = keyboard.Controller()
ms = mouse.Controller()

running = False
stop_event = threading.Event()

def hold(key, seconds):
    kb.press(key)
    time.sleep(seconds)
    kb.release(key)

def mouse_down():
    ms.press(mouse.Button.left)

def mouse_up():
    ms.release(mouse.Button.left)

def reset_character():
    print("Resetting character...")
    hold(keyboard.Key.esc, 0.05)
    time.sleep(0.2)
    hold('r', 0.05)
    time.sleep(0.2)
    hold(keyboard.Key.enter, 0.05)
   
    # Give Roblox time to respawn you at the hive
    time.sleep(3)

def walk_to_field():
    print("Walking ordered path to field...")
    hold('s', 1.0)
    hold('a', 0.5)
    hold('s', 2.0)
    print("Finished ordered path.")  

def dig_in_field():
    print("Digging in field...")

    mouse_down()  # start digging

    # simple movement pattern while digging
    hold('s', 0.75)
    hold('a', 0.75)
    hold('w', 0.75)
    hold('d', 0.75)

    mouse_up()  # stop digging

    print("Finished digging pass.")

def walk_to_hive():
    print("Walking ordered path to hive...")
    hold('w', 2.0)
    hold('d', 0.5)
    hold('w', 1.0)
    print("Finished ordered path.")  

def walk_loop():
    global running
    running = True
    stop_event.clear()

    reset_character()
    walk_to_field()
    for _ in range (5):
        dig_in_field()
    walk_to_hive()

    print("Done. Waiting for stop or quit.")
    while not stop_event.is_set():
        time.sleep(0.1)

    mouse_up()  # safety release
    running = False


def on_press(key):
    global running

    if key == keyboard.Key.f1 and not running:
        threading.Thread(target=walk_loop, daemon=True).start()

    elif key == keyboard.Key.f2 and running:
        stop_event.set()

    elif key == keyboard.Key.f3:
        print("Quitting program.")
        stop_event.set()
        return False

print("Ready. F1 = start, F2 = stop, F3 = quit. Click Roblox window before starting.")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()