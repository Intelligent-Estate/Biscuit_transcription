"""Small Win32 helpers for Biscuit."""

from __future__ import annotations

from ctypes import (
    POINTER,
    WINFUNCTYPE,
    Structure,
    Union,
    byref,
    cast,
    c_int,
    c_long,
    c_longlong,
    c_ulong,
    c_ulonglong,
    c_ushort,
    c_void_p,
    sizeof,
    windll,
)
from ctypes.wintypes import BOOL, DWORD, HHOOK, HINSTANCE, HWND, LPARAM, UINT, WPARAM
from dataclasses import dataclass
import threading
import time
from typing import Callable


WH_MOUSE_LL = 14
WM_QUIT = 0x0012
WM_RBUTTONUP = 0x0205
WM_RBUTTONDOWN = 0x0204
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_ESCAPE = 0x1B
ULONG_PTR = c_ulonglong if sizeof(c_void_p) == 8 else c_ulong
LRESULT = c_long if sizeof(c_void_p) == 4 else c_longlong


class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class MSLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KBDINPUT(Structure):
    _fields_ = [
        ("wVk", c_ushort),
        ("wScan", c_ushort),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class INPUTUNION(Union):
    _fields_ = [("ki", KBDINPUT)]


class INPUT(Structure):
    _fields_ = [("type", c_ulong), ("union", INPUTUNION)]


class MSG(Structure):
    _fields_ = [
        ("hwnd", HWND),
        ("message", UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", DWORD),
        ("pt", POINT),
    ]


LowLevelMouseProc = WINFUNCTYPE(LRESULT, c_int, WPARAM, LPARAM)

user32 = windll.user32
kernel32 = windll.kernel32

user32.GetForegroundWindow.restype = HWND
user32.SetForegroundWindow.argtypes = [HWND]
user32.SetForegroundWindow.restype = BOOL
user32.WindowFromPoint.argtypes = [POINT]
user32.WindowFromPoint.restype = HWND
user32.GetCursorPos.argtypes = [POINTER(POINT)]
user32.GetCursorPos.restype = BOOL
user32.GetWindowTextLengthW.argtypes = [HWND]
user32.GetWindowTextLengthW.restype = c_int
user32.GetWindowTextW.restype = c_int
user32.SendInput.argtypes = [UINT, c_void_p, c_int]
user32.SendInput.restype = UINT
user32.SetWindowsHookExW.argtypes = [c_int, LowLevelMouseProc, HINSTANCE, DWORD]
user32.SetWindowsHookExW.restype = HHOOK
user32.CallNextHookEx.argtypes = [HHOOK, c_int, WPARAM, LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = [HHOOK]
user32.UnhookWindowsHookEx.restype = BOOL
user32.GetMessageW.argtypes = [POINTER(MSG), HWND, UINT, UINT]
user32.GetMessageW.restype = BOOL
user32.PostThreadMessageW.argtypes = [DWORD, UINT, WPARAM, LPARAM]
user32.PostThreadMessageW.restype = BOOL
kernel32.GetCurrentThreadId.restype = DWORD
kernel32.GetModuleHandleW.argtypes = [c_void_p]
kernel32.GetModuleHandleW.restype = HINSTANCE


@dataclass(frozen=True, slots=True)
class RightClickContext:
    x: int
    y: int
    hwnd: int
    title: str
    captured_at: float


def get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(HWND(hwnd))
    if length <= 0:
        return ""
    from ctypes import create_unicode_buffer

    text = create_unicode_buffer(length + 1)
    user32.GetWindowTextW(HWND(hwnd), text, length + 1)
    return text.value


def get_cursor_pos() -> POINT:
    point = POINT()
    user32.GetCursorPos(byref(point))
    return point


def window_from_point(x: int, y: int) -> int:
    return int(user32.WindowFromPoint(POINT(x, y)))


def get_context_at(x: int, y: int) -> RightClickContext:
    hwnd = window_from_point(x, y) or int(user32.GetForegroundWindow())
    return RightClickContext(
        x=x,
        y=y,
        hwnd=hwnd,
        title=get_window_text(hwnd),
        captured_at=time.time(),
    )


def get_foreground_context() -> RightClickContext:
    point = get_cursor_pos()
    return get_context_at(point.x, point.y)


def set_foreground_window(hwnd: int) -> None:
    if hwnd:
        user32.SetForegroundWindow(HWND(hwnd))


def send_escape() -> None:
    _send_virtual_key(VK_ESCAPE)


def send_unicode_text(hwnd: int, text: str) -> int:
    if not text:
        return 0
    set_foreground_window(hwnd)
    time.sleep(0.05)
    sent = 0
    for char in text:
        code = ord(char)
        _send_unicode_char(code, key_up=False)
        _send_unicode_char(code, key_up=True)
        sent += 1
    return sent


def _send_virtual_key(vk: int) -> None:
    down = INPUT(type=INPUT_KEYBOARD, union=INPUTUNION(ki=KBDINPUT(vk, 0, 0, 0, 0)))
    up = INPUT(type=INPUT_KEYBOARD, union=INPUTUNION(ki=KBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, 0)))
    inputs = (INPUT * 2)(down, up)
    user32.SendInput(2, inputs, sizeof(INPUT))


def _send_unicode_char(code: int, key_up: bool) -> None:
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if key_up else 0)
    item = INPUT(type=INPUT_KEYBOARD, union=INPUTUNION(ki=KBDINPUT(0, code, flags, 0, 0)))
    user32.SendInput(1, byref(item), sizeof(INPUT))


class MouseHook:
    """Message-pumped low-level mouse hook."""

    def __init__(self, on_right_click: Callable[[RightClickContext], None]):
        self._on_right_click = on_right_click
        self._hook: HHOOK | None = None
        self._proc: LowLevelMouseProc | None = None
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._running = threading.Event()

    @property
    def running(self) -> bool:
        return self._running.is_set()

    def start(self) -> None:
        if self.running:
            return
        self._thread = threading.Thread(target=self._run, name="BiscuitMouseHook", daemon=True)
        self._thread.start()
        self._running.wait(timeout=2)

    def stop(self) -> None:
        if self._thread_id:
            user32.PostThreadMessageW(DWORD(self._thread_id), WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=2)
        self._running.clear()

    def _run(self) -> None:
        self._thread_id = int(kernel32.GetCurrentThreadId())

        def callback(n_code: int, w_param: WPARAM, l_param: LPARAM) -> LRESULT:
            if n_code >= 0 and int(w_param) == WM_RBUTTONUP:
                info = cast(l_param, POINTER(MSLLHOOKSTRUCT)).contents
                context = get_context_at(info.pt.x, info.pt.y)
                self._on_right_click(context)
            return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

        self._proc = LowLevelMouseProc(callback)
        self._hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._proc, kernel32.GetModuleHandleW(None), 0)
        if not self._hook:
            self._running.clear()
            return

        self._running.set()
        msg = MSG()
        while user32.GetMessageW(byref(msg), None, 0, 0) != 0:
            pass

        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
        self._running.clear()
