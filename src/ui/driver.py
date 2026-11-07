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
    send_keys(seq, with_spaces=True)
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


def menu_item(app: App, title: str):
    """Find a menu item by its label (the text includes the shortcut)."""
    for item in app.wrapper.descendants(control_type="MenuItem"):
        text = (item.window_text() or "").split("\t")[0].strip()
        if text == title:
            return item
    return None


def reset_perspective(app: App) -> None:
    window = menu_item(app, "Window")
    if window is None:
        return
    click(window)
    time.sleep(0.6)
    reset = menu_item(app, "Reset Perspective")
    if reset is None:
        send_keys_to(app, "{ESC}")
        return
    click(reset)
    time.sleep(1.0)
    for win in Desktop(backend="uia").windows(process=app.pid):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        for button in win.descendants(control_type="Button"):
            if (button.window_text() or "").strip().lower() == "ok":
                button.click_input()
                time.sleep(0.6)


def set_text(app: App, control, value: str) -> str:
    try:
        control.set_edit_text(value)
        time.sleep(0.12)
        if val(control) == value:
            return value
    except Exception:
        pass
    click(control)
    time.sleep(0.1)
    send_keys_to(app, "^a")
    send_keys_to(app, value)
    send_keys_to(app, "{TAB}")
    time.sleep(0.2)
    try:
        return val(control)
    except Exception:
        return ""


def set_field(app: App, title: str, value: str,
              control_type: str = "Edit", retries: int = 2) -> str:
    got = ""
    for _ in range(retries):
        ctrl = app.spec.child_window(title=title,
                                     control_type=control_type).wrapper_object()
        got = set_text(app, ctrl, value)
        if got == value:
            return got
        ctrl = app.spec.child_window(title=title,
                                     control_type=control_type).wrapper_object()
        got = val(ctrl)
        if got == value:
            return got
    raise RuntimeError(f"field {title!r} did not stick (got {got!r})")


def type_field(app: App, title: str, value: str,
               control_type: str = "Edit", commit=None) -> str:
    """Click, select-all and type. `commit` is a control to click to leave the
    field (Tab inserts a tab in Fakturama's multi-line edits)."""
    ctrl = app.spec.child_window(title=title,
                                 control_type=control_type).wrapper_object()
    click(ctrl)
    time.sleep(0.1)
    send_keys_to(app, "^a")
    send_keys_to(app, value)
    if commit is not None:
        click(commit)
    else:
        send_keys_to(app, "{TAB}")
    time.sleep(0.2)
    ctrl = app.spec.child_window(title=title,
                                 control_type=control_type).wrapper_object()
    got = val(ctrl)
    if got != value:
        raise RuntimeError(f"field {title!r} did not stick (got {got!r})")
    return got


def dismiss_internal_error(app: App) -> bool:
    """Close Fakturama's 'Internal Error' dialog (empty-row Ctrl+C bug)."""
    candidates = list(app.wrapper.descendants(control_type="Window"))
    candidates += list(Desktop(backend="uia").windows(process=app.pid))
    for window in candidates:
        if (window.window_text() or "").strip() != "Internal Error":
            continue
        for button in window.descendants(control_type="Button"):
            if (button.window_text() or "").strip() == "OK":
                button.click_input()
                time.sleep(0.5)
                return True
    return False


def select_combo(app: App, combo, text: str) -> str:
    wanted = text.strip()
    try:
        combo.select(wanted)
        time.sleep(0.15)
        if (combo.selected_text() or "").strip() == wanted:
            return wanted
    except Exception:
        pass

    try:
        combo.expand()
    except Exception:
        try:
            click(combo)
        except Exception:
            pass
    time.sleep(0.5)

    items = [item for item in
             app.wrapper.descendants(control_type="ListItem")
             if (item.window_text() or "").strip() == wanted]
    if not items:
        for win in Desktop(backend="uia").windows(process=app.pid):
            items += [item for item in win.descendants(control_type="ListItem")
                      if (item.window_text() or "").strip() == wanted]
    if not items:
        # Editable combo fallback: type the value directly.
        try:
            click(combo)
            send_keys_to(app, "^a")
            send_keys_to(app, wanted)
            send_keys_to(app, "{ENTER}")
            time.sleep(0.4)
            return wanted
        except Exception:
            pass
    if not items:
        raise RuntimeError(f"combo option {text!r} not found")
    click(items[0])
    time.sleep(0.35)
    return wanted
