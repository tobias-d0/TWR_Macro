import json
import time

from src.config import ROUTES_DIR, PRESS_F6_AFTER_ROUTE_IF_MISSING
from src.input_control import InputController

MOUSE_MOVE_SCALE = 1.0
KEY_EVENT_DELAY = 0.01
MOUSE_CLICK_DELAY = 0.01


class RoutePlayer:
    def __init__(self):
        self.input = InputController()

    def load_route(self, spawn_name):
        route_path = ROUTES_DIR / f"{spawn_name}.json"

        if not route_path.exists():
            raise FileNotFoundError(f"Missing route file: {route_path}")

        with open(route_path, "r") as f:
            return json.load(f)

    def route_contains_f6(self, events):
        for event in events:
            if event.get("type") in ["key_down", "key_up"]:
                if str(event.get("key", "")).lower() == "f6":
                    return True

        return False

    def release_all_keys(self, events):
        keys = set()

        for event in events:
            if event.get("type") in ["key_down", "key_up"]:
                key = event.get("key")
                if key:
                    keys.add(key)

        for key in keys:
            self.input.key_up(key)

    def play(self, spawn_name):
        events = self.load_route(spawn_name)

        print(f"Playing route: {spawn_name}")
        print(f"Events: {len(events)}")
        print(f"Mouse scale: {MOUSE_MOVE_SCALE}")

        start_time = time.perf_counter()

        try:
            for event in events:
                target_time = event.get("time", 0)

                while time.perf_counter() - start_time < target_time:
                    pass

                event_type = event.get("type")

                if event_type == "key_down":
                    self.input.key_down(event["key"])
                    time.sleep(KEY_EVENT_DELAY)

                elif event_type == "key_up":
                    self.input.key_up(event["key"])
                    time.sleep(KEY_EVENT_DELAY)

                elif event_type == "mouse_move":
                    dx = event.get("dx", 0) * MOUSE_MOVE_SCALE
                    dy = event.get("dy", 0) * MOUSE_MOVE_SCALE
                    self.input.mouse_move(dx, dy)

                elif event_type == "mouse_down":
                    self.input.mouse_down(event["button"])
                    time.sleep(MOUSE_CLICK_DELAY)

                elif event_type == "mouse_up":
                    self.input.mouse_up(event["button"])
                    time.sleep(MOUSE_CLICK_DELAY)

        finally:
            self.release_all_keys(events)

        if PRESS_F6_AFTER_ROUTE_IF_MISSING and not self.route_contains_f6(events):
            print("Route did not contain F6. Pressing F6.")
            self.input.tap_key("f6")

        print("Route finished.")