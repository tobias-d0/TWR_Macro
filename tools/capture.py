import os
import time
from datetime import datetime

import mss
from PIL import Image
from pynput import keyboard

SAVE_FOLDER = "data/raw_screenshots"
os.makedirs(SAVE_FOLDER, exist_ok=True)

running = True


def take_screenshot():
    with mss.mss() as sct:
        # monitor 1 = primary monitor
        monitor = sct.monitors[1]

        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        filename = datetime.now().strftime("capture_%Y-%m-%d_%H-%M-%S.png")
        path = os.path.join(SAVE_FOLDER, filename)

        img.save(path)
        print(f"Saved screenshot: {path}")


def on_press(key):
    global running

    try:
        if key == keyboard.Key.f4:
            take_screenshot()

        elif key == keyboard.Key.f5:
            print("Exiting screenshot tool...")
            running = False
            return False

    except Exception as e:
        print(f"Error: {e}")


print("Screenshot tool running.")
print("Press F4 to capture screenshot.")
print("Press F5 to exit.")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()