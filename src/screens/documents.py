"""Documents list and workspace/tab cleanup helpers."""
from __future__ import annotations

import time

from ..ui.driver import App, click, ensure_foreground, send_keys_to


def _menu_item(app: App, title: str):
    # Menu text includes the shortcut, e.g. "Close All\tCtrl+Shift+W".
    for item in app.wrapper.descendants(control_type="MenuItem"):
        text = (item.window_text() or "").split("\t")[0].strip()
        if text == title:
            return item
    return None


def close_all_tabs(app: App) -> None:
    """File > Close All. Call only when every document tab is saved."""
    ensure_foreground(app.hwnd, app.wrapper.rectangle())
    file_item = _menu_item(app, "File")
    if file_item is None:
        raise RuntimeError("File menu not found")
    click(file_item)
    time.sleep(0.8)
    close_all = _menu_item(app, "Close All")
    if close_all is None:
        send_keys_to(app, "{ESC}")
        raise RuntimeError("'Close All' menu item not found")
    click(close_all)
    time.sleep(1.0)


def open_documents(app: App) -> None:
    navs = [item for item in app.wrapper.descendants(control_type="Text")
            if (item.window_text() or "").strip() == "Documents"]
    navs.sort(key=lambda item: item.rectangle().left)
    if not navs:
        raise RuntimeError("Documents navigation item not found")
    click(navs[0])
    time.sleep(0.8)
