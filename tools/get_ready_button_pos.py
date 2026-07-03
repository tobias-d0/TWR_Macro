import json
import time
from pathlib import Path
from pynput import mouse

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "data" / "ready_button.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def on_click(x, y, button, pressed):
    if not pressed:
        return

    data = {
        "ready_button_pos": [x, y],
        "button": str(button).replace("Button.", "")
    }

    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved ready button position: ({x}, {y})")
    print(f"Saved to: {CONFIG_PATH}")

    return False


def main():
    print("Ready button position recorder.")
    time.sleep(3)
    print("Click the Ready/Unready button now.")

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()


if __name__ == "__main__":
    main()