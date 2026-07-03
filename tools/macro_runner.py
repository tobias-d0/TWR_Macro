import sys
import time
import threading
from pathlib import Path

from pynput import keyboard

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.macro_manager import MacroManager


manager = MacroManager()


def ask_wave_count():
    value = input("How many waves should the macro run? ").strip()

    try:
        return max(1, int(value))
    except ValueError:
        return 1
    
def ask_for_start():
    input("Press Enter to start the macro")
    print("Macro will start in 5 seconds. Switch to the game window now.")


def start_macro_thread():
    if manager.running:
        print("Macro is already running.")
        return

    wave_count = ask_wave_count()
    ask_for_start()

    time.sleep(5)

    thread = threading.Thread(
        target=manager.run,
        args=(wave_count,),
        daemon=True,
    )

    thread.start()


def on_press(key):
    if key == keyboard.Key.f4:
        start_macro_thread()

    elif key == keyboard.Key.f5:
        print("Stop requested.")
        manager.request_stop()

    elif key == keyboard.Key.f8:
        print("Exiting.")
        manager.request_stop()
        return False


def main():
    print("Macro Manager ready.")
    print("F4 = start macro")
    print("F5 = stop macro")
    print("F8 = exit program")

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    main()