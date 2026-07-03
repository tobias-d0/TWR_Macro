import json
import os
from pathlib import Path

ROUTES_DIR = Path("data/routes")


def is_f6_event(event):
    if event.get("type") not in ["key_down", "key_up"]:
        return False

    key = str(event.get("key", "")).lower()
    return key == "f6"


def clean_route(events):
    cleaned = []
    f6_pressed = False
    removed_count = 0

    for event in events:
        event_type = event.get("type")

        if event_type == "key_down" and is_f6_event(event):
            f6_pressed = True
            cleaned.append(event)
            continue

        if f6_pressed and event_type in ["mouse_down", "mouse_up"]:
            removed_count += 1
            continue

        cleaned.append(event)

    return cleaned, removed_count


def main():
    if not ROUTES_DIR.exists():
        print(f"Routes folder not found: {ROUTES_DIR}")
        return

    route_files = list(ROUTES_DIR.glob("*.json"))

    if not route_files:
        print("No route files found.")
        return

    total_removed = 0

    for route_file in route_files:
        with open(route_file, "r") as f:
            events = json.load(f)

        cleaned_events, removed = clean_route(events)

        with open(route_file, "w") as f:
            json.dump(cleaned_events, f, indent=4)

        total_removed += removed

        print(f"{route_file.name}: removed {removed} mouse click events")

    print(f"\nDone. Total removed: {total_removed}")


if __name__ == "__main__":
    main()