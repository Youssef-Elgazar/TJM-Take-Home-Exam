"""Invoice editor screen."""
from __future__ import annotations

import time

from ..ui.driver import App, val


def create_followup_invoice(app: App) -> None:
    group = app.spec.child_window(title="Create a follow-up document",
                                  control_type="Group")
    group.wait("exists", timeout=8)
    group.child_window(title="Invoice",
                       control_type="Button").click_input()
    time.sleep(0.6)
    from .order import wait_for_tab
    wait_for_tab(app, "New Invoice")


def paid_checkbox(app: App):
    return app.spec.child_window(title="paid",
                                 control_type="CheckBox").wrapper_object()


def payment_combo(app: App):
    paid = paid_checkbox(app).rectangle()
    for combo in app.wrapper.descendants(control_type="ComboBox"):
        rect = combo.rectangle()
        if abs(rect.top - paid.top) <= 15 and rect.left > paid.right:
            return combo
    return None


def set_payment_method(app: App, method: str) -> str:
    combo = payment_combo(app)
    if combo is None:
        raise RuntimeError("invoice payment-method combo not found")
    combo.select(method)
    time.sleep(0.4)
    return combo.selected_text()


def at_date_edit(app: App):
    at = app.spec.child_window(title="at",
                               control_type="Text").wrapper_object()
    lr = at.rectangle()
    candidates = []
    for edit in app.wrapper.descendants(control_type="Edit"):
        rect = edit.rectangle()
        if abs(rect.top - lr.top) <= 12 and rect.left > lr.right:
            candidates.append(edit)
    if not candidates:
        raise RuntimeError("paid-at date edit not found")
    # The date edit is the leftmost one next to the "at" label; the VAT and
    # Value edits sit much further right on the same row.
    candidates.sort(key=lambda item: item.rectangle().left)
    return candidates[0]


def set_paid(app: App, iso_date: str) -> str:
    check = paid_checkbox(app)
    try:
        state = check.get_toggle_state()
    except Exception:
        state = 0
    if state != 1:
        check.click_input()
        time.sleep(0.8)
    edit = at_date_edit(app)
    from .order import set_date
    return set_date(app, iso_date, edit=edit)


def set_value(app: App, value: str) -> str:
    from ..ui.driver import click, send_keys_to
    ctrl = app.spec.child_window(title="Value",
                                 control_type="Edit").wrapper_object()
    click(ctrl)
    time.sleep(0.2)
    send_keys_to(app, "^a")
    send_keys_to(app, value)
    send_keys_to(app, "{TAB}")
    time.sleep(0.3)
    ctrl = app.spec.child_window(title="Value",
                                 control_type="Edit").wrapper_object()
    return val(ctrl)


def read_totals(app: App) -> dict:
    from .order import read_totals as _read_totals
    return _read_totals(app)


def save(app: App) -> None:
    app.spec.child_window(title="Save the current contents",
                          control_type="Button").click_input()
    time.sleep(0.8)


def invoice_number(app: App, timeout: float = 10.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for tab in app.wrapper.descendants(control_type="TabItem"):
            title = (tab.window_text() or "").strip()
            if title.startswith("INV") and title[3:].isdigit():
                return title
        time.sleep(0.2)
    raise RuntimeError("invoice was not saved (no INV tab title)")
