import ctypes
import time
import pydirectinput

pydirectinput.PAUSE = 0
pydirectinput.MINIMUM_DURATION = 0
pydirectinput.FAILSAFE = False

SendInput = ctypes.windll.user32.SendInput

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

SCANCODES = {
    "1": 0x02, "!": 0x02,
    "2": 0x03, "@": 0x03,
    "3": 0x04, "#": 0x04,
    "4": 0x05, "$": 0x05,
    "5": 0x06, "%": 0x06,
    "6": 0x07, "^": 0x07,
    "7": 0x08, "&": 0x08,
    "8": 0x09, "*": 0x09,
    "9": 0x0A, "(": 0x0A,
    "0": 0x0B, ")": 0x0B,

    "q": 0x10,
    "w": 0x11,
    "e": 0x12,
    "r": 0x13,
    "f": 0x21,
    "a": 0x1E,
    "s": 0x1F,
    "d": 0x20,
    "c": 0x2E,

    "space": 0x39,
    "shift": 0x2A,
    "shift_l": 0x2A,
    "shift_r": 0x36,
    "ctrl": 0x1D,
    "ctrl_l": 0x1D,
    "ctrl_r": 0x1D,

    "f6": 0x40,
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


def normalize_key(key_name):
    key_name = str(key_name).lower()

    if key_name in ["shift_l", "shift_r"]:
        return key_name

    if key_name in ["ctrl_l", "ctrl_r"]:
        return key_name

    return key_name


class InputController:
    def send_scancode(self, scan_code, key_up=False):
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
            ctypes.pointer(extra),
        )

        command = Input(INPUT_KEYBOARD, ii)
        SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

    def key_down(self, key_name):
        key_name = normalize_key(key_name)

        if key_name in SCANCODES:
            self.send_scancode(SCANCODES[key_name], key_up=False)
        else:
            pydirectinput.keyDown(key_name)


    def key_up(self, key_name):
        key_name = normalize_key(key_name)

        if key_name in SCANCODES:
            self.send_scancode(SCANCODES[key_name], key_up=True)
        else:
            pydirectinput.keyUp(key_name)

    def tap_key(self, key_name, duration=0.05):
        self.key_down(key_name)
        time.sleep(duration)
        self.key_up(key_name)

    def mouse_down(self, button):
        pydirectinput.mouseDown(button=button)


    def mouse_up(self, button):
        pydirectinput.mouseUp(button=button)

    def mouse_move(self, dx, dy):
        dx = int(round(dx))
        dy = int(round(dy))

        if dx == 0 and dy == 0:
            return

        pydirectinput.moveRel(dx, dy, duration=0, relative=True)