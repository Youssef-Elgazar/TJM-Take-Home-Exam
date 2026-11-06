"""Selector dialogs: read rows by clipboard and select exact matches."""
from __future__ import annotations

import time

from pywinauto import mouse

from ..errors import ManualReviewRequired
from ..extract.ocr import run_ocr
from .driver import (DUMPS, App, click, clip_clear, clip_get,
                     dismiss_internal_error, normalise, send_keys_to_hwnd)
from .grid import address_icons, items_icons

ROW_HEIGHT = 19


def _dialog_has_rows(app: App, dialog, search_rect) -> bool:
    """OCR the table below the header; empty means copying would NPE."""
    try:
        image = dialog.capture_as_image()
        dr = dialog.rectangle()
        top = max(0, search_rect.bottom - dr.top + 34)
        bottom = max(top + 1, image.height - 95)
        crop = image.crop((0, top, image.width, bottom))
        DUMPS.mkdir(exist_ok=True)
        path = DUMPS / "dialog_rows_check.png"
        crop.save(path)
        lines = [line for line in run_ocr(path).lines
                 if (line.text or "").strip() and line.score > 0.5]
        return len(lines) > 0
    except Exception:
        return True


def _walk_rows(app: App, dialog, search_rect, max_rows: int = 25) -> list[str]:
    """Click the first row, copy it, press DOWN, repeat until empty/repeat."""
    if not _dialog_has_rows(app, dialog, search_rect):
        return []

    x = dialog.rectangle().left + 120
    y = search_rect.bottom + 40
    mouse.click(button="left", coords=(x, y))
    time.sleep(0.3)

    rows: list[str] = []
    previous = None
    for _ in range(max_rows):
        clip_clear()
        send_keys_to_hwnd(dialog.handle, "^c", dialog.rectangle())
        time.sleep(0.25)
        if dismiss_internal_error(app):
            return rows
        text = clip_get()
        if not text or text == previous:
            break
        rows.append(text)
        previous = text
        send_keys_to_hwnd(dialog.handle, "{DOWN}", dialog.rectangle())
        time.sleep(0.15)
    return rows


def _select_row(app: App, dialog, dialog_spec, rows_count: int,
                index: int) -> None:
    # Return to the first row, then step down to the target, then OK.
    for _ in range(rows_count + 1):
        send_keys_to_hwnd(dialog.handle, "{UP}", dialog.rectangle())
        time.sleep(0.04)
    for _ in range(index):
        send_keys_to_hwnd(dialog.handle, "{DOWN}", dialog.rectangle())
        time.sleep(0.04)
    dialog_spec.child_window(title="OK", control_type="Button").click_input()
    time.sleep(0.4)


def _address_fields(raw: str) -> dict | None:
    fields = [field.strip() for field in raw.split("\t")]
    if len(fields) < 9:
        return None
    return {
        "no": fields[0],
        "first_name": fields[1],
        "last_name": fields[2],
        "company": fields[3],
        "zip": fields[4],
        "city": fields[5],
        "address_type": fields[6],
        "additional": "" if fields[7] == "null" else fields[7],
        "full_name": fields[8],
    }


def select_existing_debtor(app: App, debtor) -> str:
    icons = address_icons(app)
    if not icons:
        raise ManualReviewRequired("address selector icon not found")
    click(icons[0])

    dialog_spec = app.spec.child_window(title="Select the address",
                                        control_type="Window")
    dialog_spec.wait("exists", timeout=8)
    dialog = dialog_spec.wrapper_object()
    search = dialog_spec.child_window(control_type="Edit")
    search.set_edit_text(debtor.company)
    time.sleep(1.5)

    rows = _walk_rows(app, dialog, search.rectangle())
    matches = []
    for index, raw in enumerate(rows):
        fields = _address_fields(raw)
        if fields is None:
            continue
        if (normalise(fields["company"]) == normalise(debtor.company)
                and normalise(fields["first_name"])
                == normalise(debtor.contact.first_name)
                and normalise(fields["last_name"])
                == normalise(debtor.contact.last_name)
                and normalise(fields["zip"]) == normalise(debtor.billing.zip)
                and normalise(fields["city"]) == normalise(debtor.billing.city)):
            matches.append((index, fields))

    if len(matches) != 1:
        dialog_spec.child_window(title="Cancel",
                                 control_type="Button").click_input()
        raise ManualReviewRequired(
            f"expected exactly one debtor match for {debtor.company!r}, "
            f"found {len(matches)} in {len(rows)} row(s)")

    index, fields = matches[0]
    _select_row(app, dialog, dialog_spec, len(rows), index)
    time.sleep(0.9)
    return fields["no"]


def _product_fields(raw: str) -> dict | None:
    fields = [field.strip() for field in raw.split("\t")]
    if len(fields) < 6:
        return None
    return {
        "sku": fields[0],
        "name": fields[1],
        "description": fields[2],
        "price": fields[4],
        "vat": fields[5],
    }


def select_existing_product(app: App, sku: str) -> str:
    icons = items_icons(app)
    if not icons:
        raise ManualReviewRequired("product selector icon not found")
    click(icons[0])

    dialog_spec = app.spec.child_window(title="Select a product",
                                        control_type="Window")
    dialog_spec.wait("exists", timeout=8)
    search = dialog_spec.child_window(control_type="Edit")
    search.set_edit_text(sku)
    time.sleep(1.5)

    if not dialog_spec.exists():
        return "auto-selected"

    dialog = dialog_spec.wrapper_object()
    rows = _walk_rows(app, dialog, search.rectangle())
    matches = []
    conflicts = []
    for index, raw in enumerate(rows):
        fields = _product_fields(raw)
        if fields is None:
            continue
        if fields["sku"] == sku:
            matches.append((index, fields))
        elif fields["sku"].casefold() == sku.casefold():
            conflicts.append(fields["sku"])

    if len(matches) != 1:
        dialog_spec.child_window(title="Cancel",
                                 control_type="Button").click_input()
        detail = f"found {len(matches)} exact match(es)"
        if conflicts:
            detail += f"; case conflicts: {conflicts}"
        raise ManualReviewRequired(f"product {sku!r}: {detail}")

    index, fields = matches[0]
    _select_row(app, dialog, dialog_spec, len(rows), index)
    time.sleep(0.9)
    return "selected"
