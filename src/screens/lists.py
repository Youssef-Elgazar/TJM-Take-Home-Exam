"""Generic left-nav list lookup (Products, Debtors, VATs, payments)."""
from __future__ import annotations

import time

from ..extract.ocr import run_ocr
from ..ui.driver import DUMPS, App, click, send_keys_to


def _norm(text: str) -> str:
    """Case- and whitespace-insensitive (OCR often drops spaces)."""
    return "".join((text or "").split()).casefold()


def open_list(app: App, name: str) -> None:
    navs = [item for item in app.wrapper.descendants(control_type="Text")
            if (item.window_text() or "").strip() == name]
    navs.sort(key=lambda item: item.rectangle().left)
    if not navs:
        raise RuntimeError(f"navigation item {name!r} not found")
    click(navs[0])
    time.sleep(1.2)


def list_contains(app: App, nav_name: str, text: str) -> bool:
    open_list(app, nav_name)
    edits = list(app.wrapper.descendants(control_type="Edit"))
    if not edits:
        return False
    search = max(edits, key=lambda item: item.rectangle().left)
    click(search)
    send_keys_to(app, "^a")
    send_keys_to(app, text)
    send_keys_to(app, "{TAB}")
    time.sleep(1.0)
    try:
        win = app.wrapper.rectangle()
        image = app.wrapper.capture_as_image()
        top = max(0, search.rectangle().bottom - win.top + 10)
        crop = image.crop((0, top, image.width, image.height))
        DUMPS.mkdir(exist_ok=True)
        safe = "".join(ch if ch.isalnum() else "_" for ch in nav_name)
        path = DUMPS / f"list_{safe}.png"
        crop.save(path)
        target = _norm(text)
        return any(target in _norm(line.text) for line in run_ocr(path).lines)
    except Exception:
        return False
