import os
import time
import json
import ctypes
from datetime import datetime

import mss
import pydirectinput
from PIL import Image

from src.config import READY_BUTTON_PATH

# ------------------------------------------------------------
# Windows DPI handling
# ------------------------------------------------------------

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

SAVE_FOLDER = "data/raw_screenshots"

DEFAULT_SAMPLE_COUNT = 20

STARTING_WAIT = 5
TRANSITION_WAIT = 10

# Time after resetting before toggling ready/unready
RESET_FIRST_WAIT = 30

# Remaining time for:
# wave lost screen + intermission + map loading
RESET_SECOND_WAIT = 90

# Small delays so Roblox reliably registers menu inputs
MENU_KEY_DELAY = 0.5

os.makedirs(SAVE_FOLDER, exist_ok=True)


# Remove PyDirectInput's built-in delay
pydirectinput.PAUSE = 0


class SpawnImageCollector:
    def __init__(self):
        self.ready_button_pos = self.load_ready_button_pos()

    # --------------------------------------------------------
    # Ready button
    # --------------------------------------------------------

    def load_ready_button_pos(self):
        try:
            with open(READY_BUTTON_PATH, "r") as f:
                data = json.load(f)

            pos = data.get("ready_button_pos")

            if pos and len(pos) == 2:
                return tuple(pos)

        except FileNotFoundError:
            pass

        return None

    def click_ready_button(self):
        if self.ready_button_pos is None:
            raise RuntimeError(
                "Ready button position is not configured."
            )

        x, y = self.ready_button_pos

        print(f"Clicking Ready button at ({x}, {y})")

        # Move directly onto button
        pydirectinput.moveTo(x, y, duration=0)
        time.sleep(0.25)

        # Small hover wiggle - same method as main macro
        pydirectinput.moveTo(x + 2, y, duration=0)
        time.sleep(0.05)

        pydirectinput.moveTo(x, y, duration=0)
        time.sleep(0.20)

        # Explicit mouse down/up tends to be more reliable
        pydirectinput.mouseDown(button="left")
        time.sleep(0.15)
        pydirectinput.mouseUp(button="left")

    # --------------------------------------------------------
    # Screenshot
    # --------------------------------------------------------

    def capture_spawn_image(self, sample_number):
        with mss.mss() as sct:

            # Primary monitor
            monitor = sct.monitors[1]

            screenshot = sct.grab(monitor)

            img = Image.frombytes(
                "RGB",
                screenshot.size,
                screenshot.rgb
            )

            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            filename = (
                f"sample_{sample_number:03d}_{timestamp}.png"
            )

            path = os.path.join(
                SAVE_FOLDER,
                filename
            )

            img.save(path)

            print(f"Saved screenshot:")
            print(f"  {path}")

    # --------------------------------------------------------
    # Character reset
    # --------------------------------------------------------

    def reset_character(self):
        print("Resetting character...")

        # Open Roblox menu
        pydirectinput.press("esc")
        time.sleep(MENU_KEY_DELAY)

        # Reset character
        pydirectinput.press("r")
        time.sleep(MENU_KEY_DELAY)

        # Confirm reset
        pydirectinput.press("enter")
        time.sleep(1.0)

        # # Close menu/settings if it remains open
        # pydirectinput.press("esc")
        # time.sleep(0.5)

        print("Reset sequence complete.")

    # --------------------------------------------------------
    # Countdown helper
    # --------------------------------------------------------

    def wait(self, seconds, message):
        print(f"{message} ({seconds}s)")

        end_time = time.perf_counter() + seconds

        while True:
            remaining = end_time - time.perf_counter()

            if remaining <= 0:
                break

            # Give occasional progress updates for long waits
            if remaining > 10:
                sleep_time = min(10, remaining)
            else:
                sleep_time = remaining

            time.sleep(sleep_time)

    # --------------------------------------------------------
    # Collection
    # --------------------------------------------------------

    def collect(self, sample_count):
        print()
        print("=" * 60)
        print("SPAWN IMAGE COLLECTION")
        print("=" * 60)
        print(f"Samples requested: {sample_count}")
        print(f"Save folder: {SAVE_FOLDER}")
        print()

        if self.ready_button_pos is None:
            print("ERROR: Ready button position is not configured.")
            return

        # ----------------------------------------------------
        # Initial ready
        # ----------------------------------------------------

        print("Initial ready-up...")
        self.click_ready_button()

        # ----------------------------------------------------
        # Main collection loop
        # ----------------------------------------------------

        for sample_number in range(1, sample_count + 1):

            print()
            print("=" * 60)
            print(
                f"SAMPLE {sample_number}/{sample_count}"
            )
            print("=" * 60)

            # Same timing as your normal macro
            self.wait(
                STARTING_WAIT,
                "Waiting for wave start"
            )

            self.wait(
                TRANSITION_WAIT,
                "Waiting for spawn transition"
            )

            # Capture immediately after transition
            print("Capturing spawn image...")

            self.capture_spawn_image(
                sample_number
            )

            # If that was the final image, we're done.
            if sample_number == sample_count:
                print()
                print("Final sample captured.")
                break

            # ------------------------------------------------
            # Reset
            # ------------------------------------------------

            self.reset_character()

            # First part of map/wave-lost wait
            self.wait(
                RESET_FIRST_WAIT,
                "Waiting after reset"
            )

            # Toggle ready/unready
            print("Clicking Ready/Unready button...")
            self.click_ready_button()

            # Remaining loading/intermission period
            self.wait(
                RESET_SECOND_WAIT,
                "Waiting for map/intermission"
            )

            # Ready for next spawn
            print("Readying for next sample...")
            self.click_ready_button()

        print()
        print("=" * 60)
        print("COLLECTION COMPLETE")
        print("=" * 60)
        print(f"Captured {sample_count} images.")
        print(f"Saved to: {SAVE_FOLDER}")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def get_sample_count():
    value = input(
        f"Number of spawn samples "
        f"[default {DEFAULT_SAMPLE_COUNT}]: "
    ).strip()

    if value == "":
        return DEFAULT_SAMPLE_COUNT

    try:
        count = int(value)

        if count <= 0:
            raise ValueError

        return count

    except ValueError:
        print(
            f"Invalid value. Using default "
            f"{DEFAULT_SAMPLE_COUNT}."
        )

        return DEFAULT_SAMPLE_COUNT


if __name__ == "__main__":
    sample_count = get_sample_count()

    print()
    print("IMPORTANT:")
    print("Switch to Roblox now.")
    print("Collection begins in 5 seconds.")
    print()

    time.sleep(5)

    collector = SpawnImageCollector()
    collector.collect(sample_count)