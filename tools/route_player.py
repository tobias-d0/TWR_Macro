import json
import os
import time
import pydirectinput
import ctypes

ROUTES_DIR = "data/routes"

PLAYBACK_SCALE = 1.0

KEY_EVENT_DELAY = 0.01
MOUSE_CLICK_DELAY = 0.01

pydirectinput.PAUSE = 0
pydirectinput.MINIMUM_DURATION = 0

SendInput = ctypes.windll.user32.SendInput

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

SCANCODES = {
    "1": 0x02,
    "!": 0x02,
    "2": 0x03,
    "@": 0x03,
    "3": 0x04,
    "#": 0x04,
    "4": 0x05,
    "$": 0x05,
    "5": 0x06,
    "%": 0x06,
    "6": 0x07,
    "^": 0x07,
    "7": 0x08,
    "&": 0x08,
    "8": 0x09,
    "*": 0x09,
    "9": 0x0A,
    "(": 0x0A,
    "0": 0x0B,
    ")": 0x0B,

    "w": 0x11,
    "a": 0x1E,
    "s": 0x1F,
    "d": 0x20,
    "q": 0x10,
    "e": 0x12,
    "space": 0x39,
    "shift": 0x2A,
    "ctrl": 0x1D,
    "c": 0x2E,
    "r": 0x13,
    "f": 0x21,
}
class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort),
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class Input_I(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput),
    ]


class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", Input_I),
    ]


def load_route():
    route_name = input("Enter route name to play, e.g. spawn_1: ").strip()

    if route_name.endswith(".json"):
        filename = route_name
    else:
        filename = f"{route_name}.json"

    path = os.path.join(ROUTES_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Route not found: {path}")

    with open(path, "r") as f:
        return json.load(f), path


def send_scancode(scan_code, key_up=False):
    extra = ctypes.c_ulong(0)

    flags = KEYEVENTF_SCANCODE
    if key_up:
        flags |= KEYEVENTF_KEYUP

    ii = Input_I()
    ii.ki = KeyBdInput(
        0,
        scan_code,
        flags,
        0,
        ctypes.pointer(extra)
    )

    command = Input(INPUT_KEYBOARD, ii)
    SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))


def normalize_key(key):
    key = key.lower()

    if key in ["shift_l", "shift_r"]:
        return "shift"

    if key in ["ctrl_l", "ctrl_r"]:
        return "ctrl"

    return key


def press_key(key):
    key = normalize_key(key)

    if key in SCANCODES:
        send_scancode(SCANCODES[key], key_up=False)
    else:
        pydirectinput.keyDown(key)

    time.sleep(KEY_EVENT_DELAY)


def release_key(key):
    key = normalize_key(key)

    if key in SCANCODES:
        send_scancode(SCANCODES[key], key_up=True)
    else:
        pydirectinput.keyUp(key)

    time.sleep(KEY_EVENT_DELAY)


def mouse_down(button):
    pydirectinput.mouseDown(button=button)
    time.sleep(MOUSE_CLICK_DELAY)


def mouse_up(button):
    pydirectinput.mouseUp(button=button)
    time.sleep(MOUSE_CLICK_DELAY)


def mouse_move(dx, dy):
    pydirectinput.moveRel(
        round(dx * PLAYBACK_SCALE),
        round(dy * PLAYBACK_SCALE),
        duration=0,
        relative=True
    )


def release_all_keys(events):
    keys = set()

    for event in events:
        if event.get("type") in ["key_down", "key_up"]:
            keys.add(event.get("key"))

    for key in keys:
        if key:
            pydirectinput.keyUp(key)

def play_route(events):
    print("Playing route in 3 seconds...")
    time.sleep(3)

    start = time.perf_counter()

    for event in events:
        target_time = event.get("time", 0)

        while time.perf_counter() - start < target_time:
            pass

        event_type = event.get("type")

        if event_type == "key_down":
            press_key(event["key"])

        elif event_type == "key_up":
            release_key(event["key"])

        elif event_type == "mouse_move":
            mouse_move(event["dx"], event["dy"])

        elif event_type == "mouse_down":
            mouse_down(event["button"])

        elif event_type == "mouse_up":
            mouse_up(event["button"])

    release_all_keys(events)
    print("Route finished.")


def main():
    events, path = load_route()

    print(f"Loaded route: {path}")
    print(f"Events: {len(events)}")

    play_route(events)

if __name__ == "__main__":
    main()