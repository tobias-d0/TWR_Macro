import json
import os

ROUTES_DIR = "data/routes"

files_processed = 0
events_removed = 0

for filename in os.listdir(ROUTES_DIR):
    if not filename.endswith(".json"):
        continue

    path = os.path.join(ROUTES_DIR, filename)

    with open(path, "r") as f:
        events = json.load(f)

    original_count = len(events)

    cleaned_events = [
        event for event in events
        if event.get("type") not in ("mouse_down", "mouse_up")
    ]

    removed = original_count - len(cleaned_events)
    events_removed += removed

    with open(path, "w") as f:
        json.dump(cleaned_events, f, indent=4)

    print(f"{filename}: Removed {removed} click events.")

    files_processed += 1

print("\nDone!")
print(f"Processed {files_processed} route files.")
print(f"Removed {events_removed} mouse click events.")