import sys
import time
import threading
from pathlib import Path

from pynput import keyboard

# Allows running this file from tools/
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.capture import ScreenCapture
from src.vision import SpawnDetector
from src.routes import RoutePlayer
from src.config import SPAWN_CONFIDENCE_THRESHOLD


running_macro = False


def run_macro_once():
    global running_macro

    if running_macro:
        print("Macro is already running.")
        return

    running_macro = True

    try:
        print("\nCapturing screen in 0.1 second...")
        time.sleep(0.1)

        capture = ScreenCapture()
        detector = SpawnDetector()
        player = RoutePlayer()

        image = capture.capture_bgr()

        best, top_scores = detector.detect_spawn(image)

        print("\nTop spawn matches:")
        for item in top_scores[:5]:
            print(f"{item['spawn']:10s} | {item['score']:.4f} | {item['file']}")

        spawn = best["spawn"]
        score = best["score"]

        print(f"\nDetected spawn: {spawn}")
        print(f"Confidence: {score:.4f}")

        if score < SPAWN_CONFIDENCE_THRESHOLD:
            print("Confidence too low. Not playing route.")
            return

        print("Switch focus to Roblox now if needed.")
        time.sleep(1)

        player.play(spawn)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        running_macro = False


def on_press(key):
    if key == keyboard.Key.f4:
        threading.Thread(target=run_macro_once, daemon=True).start()

    elif key == keyboard.Key.f5:
        print("Exiting test macro.")
        return False


def main():
    print("Full macro test ready.")
    print("F4 = capture screen, detect spawn, play route")
    print("F5 = exit")
    print()
    print("Before pressing F4:")
    print("- Roblox should be visible")
    print("- You should be freshly spawned")
    print("- Do not move mouse during spawn transition")
    print("- Your external autoclicker should be running/listening for F6")

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    main()