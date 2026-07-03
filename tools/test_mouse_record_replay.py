import ctypes
import time
import pydirectinput
from ctypes import wintypes

# -----------------------------
# Windows setup
# -----------------------------

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)



WM_INPUT = 0x00FF
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIDEV_INPUTSINK = 0x00000100
PM_REMOVE = 0x0001

SPI_GETMOUSE = 0x0003
SPI_SETMOUSE = 0x0004
SPIF_SENDCHANGE = 0x02

VK_F4 = 0x73
VK_ESCAPE = 0x1B

# Python 3.14 compatibility
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


# -----------------------------
# Function signatures
# -----------------------------

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

user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    WPARAM,
    LPARAM,
]
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

# -----------------------------
# Recording globals
# -----------------------------

events = []
recording = False
start_time = None


def check_error(result, message):
    if not result:
        error = ctypes.get_last_error()
        raise ctypes.WinError(error, message)


def wnd_proc(hwnd, msg, wparam, lparam):
    global start_time

    if msg == WM_INPUT and recording:
        size = wintypes.UINT(0)

        user32.GetRawInputData(
            HRAWINPUT(lparam),
            RID_INPUT,
            None,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER)
        )

        if size.value == 0:
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        buffer = ctypes.create_string_buffer(size.value)

        result = user32.GetRawInputData(
            HRAWINPUT(lparam),
            RID_INPUT,
            buffer,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER)
        )

        if result == 0xFFFFFFFF:
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents

        if raw.header.dwType == RIM_TYPEMOUSE:
            dx = raw.data.mouse.lLastX
            dy = raw.data.mouse.lLastY

            if dx != 0 or dy != 0:
                now = time.perf_counter()

                if start_time is None:
                    start_time = now

                t = now - start_time
                events.append((t, dx, dy))
                print(f"{t:.6f}  dx={dx:4d}  dy={dy:4d}")

    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def create_raw_input_window():
    h_instance = kernel32.GetModuleHandleW(None)
    class_name = "RawMouseInputWindow"

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
        "Raw Mouse Input",
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

    # Keep this reference alive so Python does not garbage collect it
    # hwnd._wndproc_ref = wndproc if hasattr(hwnd, "__dict__") else wndproc

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
        ctypes.sizeof(RAWINPUTDEVICE)
    )

    check_error(result, "RegisterRawInputDevices failed")


def pump_messages_until(end_time):
    msg = wintypes.MSG()

    while time.perf_counter() < end_time:
        while user32.PeekMessageW(
            ctypes.byref(msg),
            None,
            0,
            0,
            PM_REMOVE
        ):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        time.sleep(0.001)

def pump_messages_once():
    msg = wintypes.MSG()

    while user32.PeekMessageW(
        ctypes.byref(msg),
        None,
        0,
        0,
        PM_REMOVE
    ):
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def record_mouse(seconds=3):
    global recording, start_time, events

    events = []
    start_time = None
    recording = True

    print(f"Recording raw mouse movement for {seconds} seconds...")
    end_time = time.perf_counter() + seconds
    pump_messages_until(end_time)

    recording = False

    print(f"Recording finished. Events recorded: {len(events)}")
    return events

PLAYBACK_SCALE = 1.0

def replay_mouse(recorded_events):
    print("Replaying in 1 second...")
    time.sleep(1)

    pydirectinput.PAUSE = 0
    pydirectinput.MINIMUM_DURATION = 0

    start = time.perf_counter()

    for t, dx, dy in recorded_events:
        while time.perf_counter() - start < t:
            pass

        pydirectinput.moveRel(round(dx * PLAYBACK_SCALE), round(dy * PLAYBACK_SCALE), duration=0, relative=True)

    print("Replay finished.")







def get_mouse_settings():
    arr = (ctypes.c_int * 3)()
    user32.SystemParametersInfoW(SPI_GETMOUSE, 0, arr, 0)
    return list(arr)

def set_mouse_settings(settings):
    arr = (ctypes.c_int * 3)(*settings)
    user32.SystemParametersInfoW(SPI_SETMOUSE, 0, arr, SPIF_SENDCHANGE)

original = get_mouse_settings()

def is_key_pressed(vk_code):
    return user32.GetAsyncKeyState(vk_code) & 0x8000 != 0


def wait_for_f4():
    print("Press F4 to record/replay. Press ESC to quit.")

    while True:
        pump_messages_once()

        if is_key_pressed(VK_ESCAPE):
            return False

        if is_key_pressed(VK_F4):
            while is_key_pressed(VK_F4):
                pump_messages_once()
                time.sleep(0.01)

            return True

        time.sleep(0.01)


def main():
    hwnd, wndproc_ref = create_raw_input_window()
    register_raw_mouse(hwnd)

    original = get_mouse_settings()

    while True:
        should_continue = wait_for_f4()

        if not should_continue:
            print("Exiting.")
            break

        # Clear old raw input messages before recording
        pump_messages_once()
        time.sleep(0.05)
        pump_messages_once()

        recorded = record_mouse(seconds=3)

        print("First 10 events:")
        print(recorded[:10])

        try:
            set_mouse_settings([0, 0, 0])
            replay_mouse(recorded)
        finally:
            set_mouse_settings(original)

if __name__ == "__main__":
    main()