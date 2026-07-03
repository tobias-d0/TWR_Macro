import time
import pydirectinput

from src.capture import ScreenCapture
from src.vision import SpawnDetector
from src.routes import RoutePlayer
from src.input_control import InputController
from src.config import SPAWN_CONFIDENCE_THRESHOLD


class MacroManager:
    def __init__(self):
        self.capture = ScreenCapture()
        self.detector = SpawnDetector()
        self.player = RoutePlayer()
        self.input = InputController()

        self.running = False
        self.stop_requested = False

        self.ready_button_pos = (125, 400)  # set manually (x, y)

        self.starting_wait = 5
        self.transition_wait = 10
        self.wave_duration = 300
        self.wave_survived_wait = 11.8
        self.intermission_wait = 20

        self.spawn_retry_delay = 0.5

    def request_stop(self):
        self.stop_requested = True

    def sleep_interruptible(self, seconds):
        end = time.perf_counter() + seconds

        while time.perf_counter() < end:
            if self.stop_requested:
                return False
            time.sleep(0.05)

        return True
    def click_ready_button(self):
        if self.ready_button_pos is None:
            print("Ready button position is not set.")
            return

        x, y = self.ready_button_pos

        pydirectinput.moveTo(x, y, duration=0)
        time.sleep(0.3)

        # Small hover wiggle helps Roblox notice the cursor is over the button
        pydirectinput.moveRel(1, 0, duration=0)
        time.sleep(0.05)
        pydirectinput.moveRel(-1, 0, duration=0)
        time.sleep(0.2)

        pydirectinput.mouseDown(button="left")
        time.sleep(0.2)
        pydirectinput.mouseUp(button="left")

        time.sleep(0.2)

    def wait_for_spawn_detection(self):
        while not self.stop_requested:
            image = self.capture.capture_bgr()
            best, top_scores = self.detector.detect_spawn(image)

            print("\nTop spawn matches:")
            for item in top_scores[:5]:
                print(f"{item['spawn']:10s} | {item['score']:.4f} | {item['file']}")

            spawn = best["spawn"]
            score = best["score"]

            print(f"\nDetected spawn: {spawn}")
            print(f"Confidence: {score:.4f}")

            if score >= SPAWN_CONFIDENCE_THRESHOLD:
                return spawn

            print("Confidence too low. Probably still intermission/loading. Retrying...")
            self.sleep_interruptible(self.spawn_retry_delay)

        return None

    def run_main_loop_once(self, wave_number):
        print(f"\n=== Wave {wave_number} main loop ===")

        spawn = self.wait_for_spawn_detection()

        if spawn is None:
            return False

        if self.stop_requested:
            return False

        wave_start = time.perf_counter()

        self.player.play(spawn)

        elapsed = time.perf_counter() - wave_start
        remaining = max(0, self.wave_duration - elapsed)

        print(f"Waiting {remaining:.2f}s until wave ends")
        self.sleep_interruptible(remaining)

        print("Wave ended. Pressing Q to unrev minigun.")
        self.input.tap_key("q")

        print("Turning off autoclicker with F6.")
        self.input.tap_key("f6")

        return True

    def wait_between_waves(self):
        print("Waiting for wave survived screen...")
        if not self.sleep_interruptible(self.wave_survived_wait):
            return False

        print("Waiting for intermission...")
        if not self.sleep_interruptible(self.intermission_wait):
            return False

        print("Waiting for next wave starting...")
        if not self.sleep_interruptible(self.starting_wait):
            return False
        
        print("Waiting for transition...")
        if not self.sleep_interruptible(self.transition_wait):
            return False

        return True

    def keep_alive_after_finished(self):
        print("Finished requested waves.")
        print("Pressing ready/unready button if configured.")

        self.click_ready_button()

        print("Moving mouse to centre and turning autoclicker back on.")
        pydirectinput.moveTo(960, 540)
        self.input.tap_key("f6")

    def run(self, wave_count):
        if self.running:
            print("Macro is already running.")
            return

        self.running = True
        self.stop_requested = False

        try:
            print("\nMacro starting.")
            print(f"Requested waves: {wave_count}")

            print("Clicking ready button.")
            self.click_ready_button()

            print("Waiting for wave start...")
            if not self.sleep_interruptible(self.starting_wait):
                return
            print("Waiting for transition...")
            if not self.sleep_interruptible(self.transition_wait):
                return

            # Capture/recognise immediately
            for wave_number in range(1, wave_count + 1):
                if self.stop_requested:
                    break

                ok = self.run_main_loop_once(wave_number)

                if not ok:
                    break

                if wave_number < wave_count:
                    ok = self.wait_between_waves()

                    if not ok:
                        break

            if not self.stop_requested:
                self.keep_alive_after_finished()

        except Exception as e:
            print(f"Macro error: {e}")

        finally:
            self.running = False
            print("Macro stopped.")