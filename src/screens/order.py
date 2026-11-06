"""Order editor screen."""
from __future__ import annotations

import time

from pywinauto import mouse

from ..ui.driver import App, click, label, parse_money, send_keys_to, val
from ..ui.grid import (cell_xy, edit_cell, grid_rect, items_icons,
                       read_row_amounts)
from ..ui.selectors import select_existing_product

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def open_new_order(app: App) -> None:
    # Reuse a leftover New Order instead of stacking a second one.
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            time.sleep(0.9)
            return
    app.spec.child_window(title="Create: New Order",
                          control_type="Button").click_input()
    time.sleep(2.0)
    wait_for_tab(app, "New Order")


def wait_for_tab(app: App, name: str, timeout: float = 8.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        titles = [tab.window_text() or ""
                  for tab in app.wrapper.descendants(control_type="TabItem")]
        if any(title.lstrip("*") == name for title in titles):
            return
        time.sleep(0.2)
    raise RuntimeError(f"tab {name!r} did not appear")


def date_edit(app: App):
    lr = label(app.spec, "Date").rectangle()
    for edit in app.wrapper.descendants(control_type="Edit"):
        rect = edit.rectangle()
        if abs(rect.top - lr.top) <= 10 and rect.left > lr.right:
            return edit
    raise RuntimeError("order date edit not found")


def set_date(app: App, iso_date: str, edit=None) -> str:
    year, month, day = (int(part) for part in iso_date.split("-"))
    edit = edit or date_edit(app)
    rect = edit.rectangle()
    ymid = (rect.top + rect.bottom) // 2
    width = rect.width()
    for dx, text in ((int(width * 0.62), str(year)),
                     (int(width * 0.19), str(month)),
                     (int(width * 0.04), str(day))):
        mouse.click(button="left", coords=(rect.left + dx, ymid))
        time.sleep(0.2)
        send_keys_to(app, text)
        time.sleep(0.2)
    # Commit the segmented field by moving focus to Cust.Ref.
    ref = app.spec.child_window(title="Cust.Ref.",
                                control_type="Edit").wrapper_object()
    click(ref)
    time.sleep(0.5)
    got = val(edit)
    expected = f"{day} {MONTHS[month - 1]} {year}"
    if got != expected:
        raise RuntimeError(
            f"date did not stick: expected {expected!r}, got {got!r}")
    return got


def set_cust_ref(app: App, value: str) -> str:
    got = ""
    for _ in range(2):
        ref = app.spec.child_window(title="Cust.Ref.",
                                    control_type="Edit").wrapper_object()
        click(ref)
        time.sleep(0.2)
        send_keys_to(app, "^a")
        send_keys_to(app, value)
        send_keys_to(app, "{TAB}")
        time.sleep(0.3)
        ref = app.spec.child_window(title="Cust.Ref.",
                                    control_type="Edit").wrapper_object()
        got = ref.get_value()
        if got == value:
            return got
    raise RuntimeError(f"Cust.Ref. did not stick: {got!r}")


def mode_combo(app: App):
    lr = label(app.spec, "Date").rectangle()
    date_rect = date_edit(app).rectangle()
    for combo in app.wrapper.descendants(control_type="ComboBox"):
        rect = combo.rectangle()
        if abs(rect.top - lr.top) <= 10 and rect.left > date_rect.right:
            return combo
    return None


def set_net_mode(app: App) -> str:
    combo = mode_combo(app)
    if combo is None:
        raise RuntimeError("price-mode combo not found")
    try:
        combo.select("Net")
    except Exception:
        click(combo)
        time.sleep(0.3)
        send_keys_to(app, "Net")
        send_keys_to(app, "{ENTER}")
    time.sleep(0.5)
    try:
        return combo.selected_text()
    except Exception:
        return ""


def clear_all_lines(app: App, max_lines: int = 20) -> None:
    """Remove every line from the open order (safe for re-runs)."""
    grid = grid_rect(app)
    for _ in range(max_lines):
        totals = read_totals(app)
        if not totals.get("Total Net"):
            return
        x, y = cell_xy(app, 1, "pos", grid)
        mouse.click(button="left", coords=(x, y))
        time.sleep(0.2)
        icons = items_icons(app)
        if len(icons) < 3:
            raise RuntimeError("red-x icon not found")
        click(icons[2])
        time.sleep(0.4)


def add_order_line(app: App, item, row: int) -> dict:
    select_existing_product(app, item.sku)
    time.sleep(0.8)
    edit_cell(app, row, "qty", _number(item.qty))
    edit_cell(app, row, "u_price", _number(item.unit_net))
    edit_cell(app, row, "discount", _number(item.discount_pct))
    return read_row_amounts(app, row)


def _number(value) -> str:
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}"


def read_totals(app: App) -> dict:
    totals = {}
    for name in ("Total Net", "Discount", "VAT", "Total"):
        try:
            ctrl = app.spec.child_window(title=name,
                                         control_type="Edit").wrapper_object()
            totals[name] = parse_money(val(ctrl))
        except Exception:
            totals[name] = None
    return totals


def save(app: App) -> None:
    app.spec.child_window(title="Save the current contents",
                          control_type="Button").click_input()
    time.sleep(1.5)


def saved_order_number(app: App, timeout: float = 10.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for tab in app.wrapper.descendants(control_type="TabItem"):
            title = (tab.window_text() or "").strip()
            if title.startswith("PO") and title[2:].isdigit():
                return title
        time.sleep(0.2)
    raise RuntimeError("order was not saved (no PO tab title)")
