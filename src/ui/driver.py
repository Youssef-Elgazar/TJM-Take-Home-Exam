"""UIA driver primitives for Fakturama."""
from __future__ import annotations

import ctypes
import re
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys

ROOT = Path(__file__).resolve().parents[2]
DUMPS = ROOT / "dumps"

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND,
                                            ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD,
                                     wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL

_MONEY_RE = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass
class App:
    spec: object
    wrapper: object
    hwnd: int
    pid: int


def get_app(timeout: float = 15.0) -> App:
    spec = Desktop(backend="uia").window(title_re=r"^Fakturama - .*")
    spec.wait("exists", timeout=timeout)
    wrapper = spec.wrapper_object()
    try:
        if wrapper.is_minimized():
            wrapper.restore()
            time.sleep(0.5)
    except Exception:
        pass
    force_foreground(wrapper.handle)
    time.sleep(0.3)
    return App(spec=spec, wrapper=wrapper, hwnd=wrapper.handle,
               pid=wrapper.process_id())


def force_foreground(hwnd: int) -> bool:
    if user32.GetForegroundWindow() == hwnd:
        return True
    fg = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg, None)
    our_thread = user32.GetWindowThreadProcessId(hwnd, None)
    try:
        user32.AttachThreadInput(fg_thread, our_thread, True)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.AttachThreadInput(fg_thread, our_thread, False)
    except Exception:
        pass
    time.sleep(0.3)
    return user32.GetForegroundWindow() == hwnd


def ensure_foreground(hwnd: int, rect=None) -> None:
    if user32.GetForegroundWindow() == hwnd:
        return
    force_foreground(hwnd)
    if user32.GetForegroundWindow() == hwnd:
        return
    if rect is not None:
        # A real click on the title bar also defeats the foreground lock.
        mouse.click(button="left", coords=(rect.left + 300, rect.top + 12))
        time.sleep(0.4)
    if user32.GetForegroundWindow() != hwnd:
        raise RuntimeError(
            f"window {hwnd} is not in the foreground "
            f"(foreground={user32.GetForegroundWindow()})")


def _process_id(hwnd: int) -> int:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def send_keys_to_hwnd(hwnd: int, seq: str, rect=None) -> None:
    """Send keys if the foreground window belongs to the target's process.

    A focused SWT edit is a child HWND, so comparing exact handles would skip
    valid keystrokes. Comparing process IDs keeps the safety guard (the
    terminal is a different process) while allowing child controls.
    """
    foreground = user32.GetForegroundWindow()
    if (foreground != hwnd
            and _process_id(foreground) != _process_id(hwnd)):
        ensure_foreground(hwnd, rect)
        foreground = user32.GetForegroundWindow()
        if (foreground != hwnd
                and _process_id(foreground) != _process_id(hwnd)):
            raise RuntimeError(
                f"window {hwnd} is not in the foreground "
                f"(foreground={foreground}, pid={_process_id(foreground)})")
    send_keys(seq)
    time.sleep(0.05)


def send_keys_to(app: App, seq: str) -> None:
    send_keys_to_hwnd(app.hwnd, seq, app.wrapper.rectangle())


def center(ctrl) -> tuple[int, int]:
    rect = ctrl.rectangle()
    return ((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)


def click(ctrl, double: bool = False) -> None:
    x, y = center(ctrl)
    if double:
        mouse.double_click(button="left", coords=(x, y))
    else:
        mouse.click(button="left", coords=(x, y))


def label(spec, text: str):
    return spec.child_window(title=text,
                             control_type="Text").wrapper_object()


def val(ctrl) -> str:
    try:
        return ctrl.get_value()
    except Exception:
        return ""


def snap(app: App, name: str) -> None:
    try:
        DUMPS.mkdir(exist_ok=True)
        image = app.wrapper.capture_as_image()
        if image is not None:
            image.save(DUMPS / f"{name}.png")
    except Exception:
        pass


def _open_clipboard(retries: int = 50) -> None:
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return
        time.sleep(0.02)
    raise RuntimeError("could not open the clipboard")


def clip_clear() -> None:
    _open_clipboard()
    try:
        user32.EmptyClipboard()
    finally:
        user32.CloseClipboard()


def clip_get() -> str:
    _open_clipboard()
    try:
        handle = user32.GetClipboardData(13)  # CF_UNICODETEXT
        if not handle:
            return ""
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return ""
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def parse_money(text: str | None) -> float | None:
    if text is None:
        return None
    match = _MONEY_RE.search(str(text).replace(",", ""))
    return float(match.group(0)) if match else None


def normalise(text: str | None) -> str:
    return " ".join((text or "").split()).casefold()
