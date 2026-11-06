import ctypes
import faulthandler
import os
import sys
import time
import traceback
from ctypes import wintypes

from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys

os.makedirs("dumps", exist_ok=True)
faulthandler.enable(open("dumps/fault.txt", "w"))
_log_file = None


def start_log(name):
    global _log_file
    _log_file = open(f"dumps/{name}_log.txt", "w", encoding="utf-8")


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    if _log_file:
        _log_file.write(msg + "\n")
        _log_file.flush()


# ---- clipboard through the Windows API (tkinter crashed) ----
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.GetForegroundWindow.restype = wintypes.HWND
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND,
                                            ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD,
                                     wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL


def force_foreground(hwnd):
    """Best-effort SetForegroundWindow, bypassing the foreground lock."""
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
    time.sleep(0.4)
    return user32.GetForegroundWindow() == hwnd


def _open_clipboard(retries=50):
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return
        time.sleep(0.02)
    raise RuntimeError("could not open the clipboard")


def clip_clear():
    _open_clipboard()
    try:
        user32.EmptyClipboard()
    finally:
        user32.CloseClipboard()


def clip_get():
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


# ---- UI helpers ----
def get_app(timeout=15):
    # Anchored so a terminal/window whose title merely contains "Fakturama"
    # (e.g. "OC | Fakturama handover tasks") is not matched.
    spec = Desktop(backend="uia").window(title_re=r"^Fakturama - .*")
    spec.wait("exists", timeout=timeout)
    w = spec.wrapper_object()
    try:
        if w.is_minimized():
            w.restore()
            time.sleep(0.5)
    except Exception:
        pass
    force_foreground(w.handle)
    time.sleep(0.4)
    return spec, w


def snap(w, name):
    try:
        img = w.capture_as_image()
        if img is not None:
            img.save(f"dumps/{name}.png")
    except Exception as e:
        log("  !! snapshot failed:", repr(e))


def keys(win, seq):
    """Send keys only if `win` is the foreground window (Ctrl+C elsewhere kills Python)."""
    if user32.GetForegroundWindow() != win.handle:
        log("  !! expected window not in foreground, skipping keys:", seq)
        return False
    send_keys(seq)
    return True


def center(ctrl):
    r = ctrl.rectangle()
    return ((r.left + r.right) // 2, (r.top + r.bottom) // 2)


def click(ctrl, double=False):
    x, y = center(ctrl)
    if double:
        mouse.double_click(button="left", coords=(x, y))
    else:
        mouse.click(button="left", coords=(x, y))


def label(spec, text):
    return spec.child_window(title=text, control_type="Text").wrapper_object()


def val(ctrl):
    try:
        return ctrl.get_value()
    except Exception:
        return ""


def _icons(spec, w, label_text, left_lo, left_hi, dy_max):
    lr = label(spec, label_text).rectangle()
    found = []
    for img in w.descendants(control_type="Image"):
        r = img.rectangle()
        if left_lo(lr) <= r.left <= left_hi(lr) and lr.bottom <= r.top <= lr.bottom + dy_max:
            found.append(img)
    return sorted(found, key=lambda i: i.rectangle().top)


def items_icons(spec, w):
    """[product selector, green +, red x, copy], top to bottom."""
    return _icons(spec, w, "Items", lambda lr: lr.left - 2, lambda lr: lr.right, 140)


def address_icons(spec, w):
    """[existing contact selector, green +], top to bottom."""
    return _icons(spec, w, "Addresses", lambda lr: lr.left, lambda lr: lr.right, 80)


def grid_rect(spec, w):
    lr = label(spec, "Items").rectangle()
    best = None
    for p in w.descendants(control_type="Pane"):
        r = p.rectangle()
        if r.left >= lr.right and abs(r.top - lr.top) <= 3 and r.width() > 800:
            area = r.width() * r.height()
            if best is None or area > best[0]:
                best = (area, r)
    return best[1] if best else None


def run(main):
    try:
        main()
    except BaseException:
        log("CRASHED:\n" + traceback.format_exc())
        sys.exit(1)
