import ctypes
import json
import os
import time
from ctypes import wintypes
from pynput import keyboard, mouse

ROUTES_DIR = "data/routes"
os.makedirs(ROUTES_DIR, exist_ok=True)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WM_INPUT = 0x00FF
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIDEV_INPUTSINK = 0x00000100
PM_REMOVE = 0x0001

VK_F4 = 0x73
VK_F5 = 0x74

LRESULT = ctypes.c_ssize_t
WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
HRAWINPUT = wintypes.HANDLE
LPVOID = ctypes.c_void_p


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", WPARAM),
    ]


class RAWMOUSE_BUTTONS_STRUCT(ctypes.Structure):
    _fields_ = [
        ("usButtonFlags", wintypes.USHORT),
        ("usButtonData", wintypes.USHORT),
    ]


class RAWMOUSE_BUTTONS_UNION(ctypes.Union):
    _fields_ = [
        ("ulButtons", wintypes.ULONG),
        ("buttons", RAWMOUSE_BUTTONS_STRUCT),
    ]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("buttons", RAWMOUSE_BUTTONS_UNION),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]


class RAWHID(ctypes.Structure):
    _fields_ = [
        ("dwSizeHid", wintypes.DWORD),
        ("dwCount", wintypes.DWORD),
        ("bRawData", wintypes.BYTE * 1),
    ]


class RAWINPUTDATA(ctypes.Union):
    _fields_ = [
        ("mouse", RAWMOUSE),
        ("keyboard", RAWKEYBOARD),
        ("hid", RAWHID),
    ]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", RAWINPUTDATA),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    WPARAM,
    LPARAM
)


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
user32.RegisterClassW.restype = wintypes.ATOM

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT

user32.RegisterRawInputDevices.argtypes = [
    ctypes.POINTER(RAWINPUTDEVICE),
    wintypes.UINT,
    wintypes.UINT,
]
user32.RegisterRawInputDevices.restype = wintypes.BOOL

user32.GetRawInputData.argtypes = [
    HRAWINPUT,
    wintypes.UINT,
    LPVOID,
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT,
]
user32.GetRawInputData.restype = wintypes.UINT

user32.PeekMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
    wintypes.UINT,
]
user32.PeekMessageW.restype = wintypes.BOOL

user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.TranslateMessage.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = LRESULT

user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short


events = []
recording = False
start_time = None
pressed_keys = set()


def now():
    return round(time.perf_counter() - start_time, 4)


def check_error(result, message):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error(), message)


def key_to_string(key):
    try:
        return key.char
    except AttributeError:
        return str(key).replace("Key.", "")


def save_route():
    route_name = input("\nEnter route name, e.g. spawn_1: ").strip()

    if not route_name:
        route_name = "unnamed_route"

    path = os.path.join(ROUTES_DIR, f"{route_name}.json")

    with open(path, "w") as f:
        json.dump(events, f, indent=4)

    print(f"Saved route to: {path}")
    print(f"Recorded {len(events)} events.")


def on_key_press(key):
    if not recording:
        return

    if key in [keyboard.Key.f4, keyboard.Key.f5]:
        return

    key_name = key_to_string(key)

    if key_name in pressed_keys:
        return

    pressed_keys.add(key_name)

    events.append({
        "time": now(),
        "type": "key_down",
        "key": key_name,
    })

    print(f"{now():>7} key_down {key_name}")


def on_key_release(key):
    if not recording:
        return

    if key in [keyboard.Key.f4, keyboard.Key.f5]:
        return

    key_name = key_to_string(key)
    pressed_keys.discard(key_name)

    events.append({
        "time": now(),
        "type": "key_up",
        "key": key_name,
    })

    print(f"{now():>7} key_up   {key_name}")


def on_mouse_click(x, y, button, pressed):
    if not recording:
        return

    button_name = str(button).replace("Button.", "")

    events.append({
        "time": now(),
        "type": "mouse_down" if pressed else "mouse_up",
        "button": button_name,
    })

    print(f"{now():>7} mouse {'down' if pressed else 'up'} {button_name}")


def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_INPUT and recording:
        size = wintypes.UINT(0)

        user32.GetRawInputData(
            HRAWINPUT(lparam),
            RID_INPUT,
            None,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )

        if size.value == 0:
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        buffer = ctypes.create_string_buffer(size.value)

        result = user32.GetRawInputData(
            HRAWINPUT(lparam),
            RID_INPUT,
            buffer,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )

        if result == 0xFFFFFFFF:
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents

        if raw.header.dwType == RIM_TYPEMOUSE:
            dx = raw.data.mouse.lLastX
            dy = raw.data.mouse.lLastY

            if dx != 0 or dy != 0:
                events.append({
                    "time": now(),
                    "type": "mouse_move",
                    "dx": dx,
                    "dy": dy,
                })

    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def create_raw_input_window():
    h_instance = kernel32.GetModuleHandleW(None)
    class_name = "RawRouteRecorderWindow"

    wndproc = WNDPROC(wnd_proc)

    wc = WNDCLASS()
    wc.lpfnWndProc = wndproc
    wc.hInstance = h_instance
    wc.lpszClassName = class_name

    atom = user32.RegisterClassW(ctypes.byref(wc))
    check_error(atom, "RegisterClassW failed")

    hwnd = user32.CreateWindowExW(
        0,
        class_name,
        "Raw Route Recorder",
        0,
        0,
        0,
        0,
        0,
        None,
        None,
        h_instance,
        None,
    )

    check_error(hwnd, "CreateWindowExW failed")

    return hwnd, wndproc


def register_raw_mouse(hwnd):
    rid = RAWINPUTDEVICE()
    rid.usUsagePage = 0x01
    rid.usUsage = 0x02
    rid.dwFlags = RIDEV_INPUTSINK
    rid.hwndTarget = hwnd

    result = user32.RegisterRawInputDevices(
        ctypes.byref(rid),
        1,
        ctypes.sizeof(RAWINPUTDEVICE),
    )

    check_error(result, "RegisterRawInputDevices failed")


def pump_messages_once():
    msg = wintypes.MSG()

    while user32.PeekMessageW(
        ctypes.byref(msg),
        None,
        0,
        0,
        PM_REMOVE,
    ):
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def is_key_pressed(vk_code):
    return (user32.GetAsyncKeyState(vk_code) & 0x8000) != 0


def wait_for_key_release(vk_code):
    while is_key_pressed(vk_code):
        pump_messages_once()
        time.sleep(0.01)


def clear_message_queue():
    pump_messages_once()
    time.sleep(0.05)
    pump_messages_once()


def start_recording():
    global recording, events, start_time, pressed_keys

    events = []
    pressed_keys = set()
    start_time = time.perf_counter()

    clear_message_queue()

    recording = True

    print("\nRecording started.")
    print("Press F4 again to stop and save.")


def stop_recording():
    global recording

    recording = False

    clear_message_queue()

    print("\nRecording stopped.")
    save_route()


def main():
    hwnd, wndproc_ref = create_raw_input_window()
    register_raw_mouse(hwnd)

    keyboard_listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release,
    )

    mouse_listener = mouse.Listener(
        on_click=on_mouse_click,
    )

    keyboard_listener.start()
    mouse_listener.start()

    print("Route recorder ready.")
    print("F4 = start/stop recording")
    print("F5 = exit")
    print("Mouse movement is recorded using Windows Raw Input.")
    print()

    running = True

    while running:
        pump_messages_once()

        if is_key_pressed(VK_F4):
            wait_for_key_release(VK_F4)

            if not recording:
                start_recording()
            else:
                stop_recording()

        if is_key_pressed(VK_F5):
            wait_for_key_release(VK_F5)

            if recording:
                stop_recording()

            print("Exiting recorder.")
            running = False

        time.sleep(0.001)

    keyboard_listener.stop()
    mouse_listener.stop()


if __name__ == "__main__":
    main()