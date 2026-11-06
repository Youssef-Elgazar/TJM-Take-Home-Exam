"""Items grid geometry and clipboard read/write helpers.

The grid is custom-drawn, so cells are located by local image processing only
(no LLM round-trip): column x-centres come from OCR of the header labels, and
row y-centres from OCR of the ``Pos`` numbers, with an OpenCV horizontal-line
fallback when the row numbers are not recognised.
"""
from __future__ import annotations

import re
import time

from pywinauto import mouse

from ..extract.ocr import run_ocr
from .driver import (DUMPS, App, clip_clear, clip_get, label, parse_money,
                     send_keys_to)

# Fallback column x-offsets for a 1700px-wide window. Real runs derive them
# from the header row with OCR (see grid_columns).
COLUMNS = {
    "pos": 20,
    "qty": 90,
    "item_no": 150,
    "name": 250,
    "description": 350,
    "vat": 450,
    "u_price": 690,
    "discount": 790,
    "price": 890,
}
ROW_HEIGHT = 20
ROW_TOP = 31


def _icons(app: App, label_text: str, dy_max: float):
    spec, wrapper = app.spec, app.wrapper
    lr = label(spec, label_text).rectangle()
    found = []
    for image in wrapper.descendants(control_type="Image"):
        rect = image.rectangle()
        if (lr.left - 2 <= rect.left <= lr.right
                and lr.bottom <= rect.top <= lr.bottom + dy_max):
            found.append(image)
    return sorted(found, key=lambda item: item.rectangle().top)


def items_icons(app: App) -> list:
    """[product selector, green +, red x, copy], top to bottom."""
    return _icons(app, "Items", 140)


def address_icons(app: App) -> list:
    """[existing-contact selector, green +], top to bottom."""
    return _icons(app, "Addresses", 80)


def grid_rect(app: App):
    lr = label(app.spec, "Items").rectangle()
    best = None
    for pane in app.wrapper.descendants(control_type="Pane"):
        rect = pane.rectangle()
        if (rect.left >= lr.right and abs(rect.top - lr.top) <= 3
                and rect.width() > 800):
            area = rect.width() * rect.height()
            if best is None or area > best[0]:
                best = (area, rect)
    return best[1] if best else None


_COLUMN_CACHE: dict = {}


def _header_key(text: str) -> str | None:
    compact = re.sub(r"[^a-z]", "", (text or "").lower())
    for prefix, name in (("pos", "pos"), ("qty", "qty"), ("upri", "u_price"),
                         ("discount", "discount"), ("price", "price"),
                         ("vat", "vat"), ("item", "item_no"),
                         ("name", "name"), ("description", "description")):
        if compact.startswith(prefix):
            return name
    return None


def grid_columns(app: App, grid=None) -> dict:
    """Read the grid header with OCR and return column centres.

    Offsets are relative to the grid's left edge. Falls back to the measured
    defaults if OCR is unavailable.
    """
    grid = grid or grid_rect(app)
    if grid is None:
        return dict(COLUMNS)
    cache_key = (grid.left, grid.top, grid.right)
    if cache_key in _COLUMN_CACHE:
        return _COLUMN_CACHE[cache_key]

    columns = dict(COLUMNS)
    try:
        win = app.wrapper.rectangle()
        image = app.wrapper.capture_as_image()
        header = image.crop((grid.left - win.left, grid.top - win.top,
                             grid.right - win.left, grid.top - win.top + 34))
        DUMPS.mkdir(exist_ok=True)
        path = DUMPS / "grid_header.png"
        header.save(path)
        for line in run_ocr(path).lines:
            if line.top > 28:
                continue
            name = _header_key(line.text)
            if name:
                columns[name] = (line.left + line.right) / 2.0
        _COLUMN_CACHE.clear()
        _COLUMN_CACHE[cache_key] = columns
    except Exception:
        pass
    return columns


_ROW_CACHE: dict = {}


def _row_centers_via_lines(gray) -> list[float]:
    """Best-effort row centres from the grid's horizontal separator lines.

    Used only when OCR cannot read the ``Pos`` numbers. The grid draws a
    horizontal line under every row, so the y-centre of each row is the
    midpoint between two consecutive lines (skipping the header separator).
    """
    import cv2
    import numpy as np

    arr = np.asarray(gray)
    if arr.ndim == 3:
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(arr, 50, 150)
    hkernel = cv2.getStructuringElement(cv2.MORPH_RECT,
                                        (max(2, arr.shape[1] // 2), 1))
    horizontal = cv2.morphologyEx(edges, cv2.MORPH_OPEN, hkernel)
    row_sum = horizontal.sum(axis=1)
    ys = [int(i) for i in range(len(row_sum)) if row_sum[i] > 0]
    if not ys:
        return []
    bounds: list[float] = []
    start = prev = ys[0]
    for y in ys[1:]:
        if y - prev > 3:
            bounds.append((start + prev) / 2.0)
            start = y
        prev = y
    bounds.append((start + prev) / 2.0)
    return [(bounds[i - 1] + bounds[i]) / 2.0 for i in range(1, len(bounds))]


def grid_row_centers(app: App, grid, force: bool = False) -> dict:
    """Map each ``Pos`` number to its row's y-centre (variable-height rows).

    Reads the ``Pos`` column with OCR; if no row numbers are recognised it
    falls back to OpenCV horizontal-line detection, which yields the same
    centres in reading order (1, 2, 3, ...).
    """
    cache_key = (grid.left, grid.top, grid.right, grid.bottom)
    if not force and cache_key in _ROW_CACHE:
        return _ROW_CACHE[cache_key]
    centers: dict[int, float] = {}
    try:
        win = app.wrapper.rectangle()
        image = app.wrapper.capture_as_image()
        crop = image.crop((grid.left - win.left, grid.top - win.top,
                           grid.right - win.left, grid.bottom - win.top))
        DUMPS.mkdir(exist_ok=True)
        path = DUMPS / "grid_rows.png"
        crop.save(path)
        for line in run_ocr(path).lines:
            text = (line.text or "").strip()
            if text.isdigit() and line.left < 45:
                centers[int(text)] = (line.top + line.bottom) / 2.0
        if not centers:
            fallback = _row_centers_via_lines(crop.convert("L"))
            # The first detected band is the header; data rows follow in order.
            centers = {i: cy for i, cy in enumerate(fallback[1:], start=1)}
        _ROW_CACHE.clear()
        _ROW_CACHE[cache_key] = centers
    except Exception:
        pass
    return centers


def cell_xy(app: App, row: int, column: str, grid=None):
    grid = grid or grid_rect(app)
    if grid is None:
        raise RuntimeError("items grid not found")

    columns = grid_columns(app, grid)
    centers = grid_row_centers(app, grid)
    if row not in centers:
        # A line was added after the cache was built; recompute.
        centers = grid_row_centers(app, grid, force=True)
    y_offset = centers.get(row, ROW_TOP + ROW_HEIGHT * (row - 1))
    return (int(round(grid.left + columns.get(column, COLUMNS[column]))),
            int(round(grid.top + y_offset)))


def read_row(app: App, row: int, grid=None) -> list[str]:
    x, y = cell_xy(app, row, "pos", grid)
    mouse.click(button="left", coords=(x, y))
    time.sleep(0.3)
    clip_clear()
    send_keys_to(app, "^c")
    time.sleep(0.25)
    return (clip_get() or "").split("\t")


def read_row_amounts(app: App, row: int, grid=None) -> dict:
    fields = read_row(app, row, grid)
    return {
        "qty": parse_money(fields[0]) if len(fields) > 0 else None,
        "sku": fields[1].strip() if len(fields) > 1 else "",
        "unit_price": parse_money(fields[6]) if len(fields) > 6 else None,
        "discount": parse_money(fields[7]) if len(fields) > 7 else None,
        "line_price": parse_money(fields[8]) if len(fields) > 8 else None,
    }


def wait_for_row(app: App, row: int, sku: str,
                 timeout: float = 12.0) -> dict:
    """Wait until the newly added line is rendered and readable at `row`."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        grid = grid_rect(app)  # the items area grows when a line is added
        if grid is None:
            time.sleep(0.3)
            continue
        centers = grid_row_centers(app, grid, force=True)
        if row in centers:
            amounts = read_row_amounts(app, row, grid)
            if (amounts.get("sku") or "").strip() == (sku or "").strip():
                return amounts
        time.sleep(0.4)
    raise RuntimeError(f"row {row} ({sku!r}) did not appear")


def _edit_handles(app: App) -> set:
    return {edit.handle for edit in
            app.wrapper.descendants(control_type="Edit")}


def edit_cell(app: App, row: int, column: str, text: str,
              grid=None) -> None:
    x, y = cell_xy(app, row, column, grid)
    before = _edit_handles(app)
    mouse.double_click(button="left", coords=(x, y))
    inline = []
    deadline = time.time() + 3.0
    while time.time() < deadline:
        inline = [edit for edit in
                  app.wrapper.descendants(control_type="Edit")
                  if edit.handle not in before]
        if inline:
            break
        time.sleep(0.1)
    if not inline:
        raise RuntimeError(
            f"no inline editor appeared for row {row}, column {column}")
    send_keys_to(app, "^a")
    send_keys_to(app, text)
    send_keys_to(app, "{ENTER}")
    time.sleep(0.3)
