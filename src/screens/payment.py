"""Terms-of-payment (payment method) creation."""
from __future__ import annotations

import time

from ..ui.driver import App, click, select_combo, set_field, set_text, val
from .lists import list_contains


def open_terms_of_payment(app: App) -> None:
    navs = [item for item in app.wrapper.descendants(control_type="Text")
            if (item.window_text() or "").strip() == "terms of payment"]
    navs.sort(key=lambda item: item.rectangle().left)
    if not navs:
        raise RuntimeError("terms of payment navigation not found")
    click(navs[0])
    time.sleep(1.2)


def payment_method_exists(app: App, name: str) -> bool:
    return list_contains(app, "terms of payment", name)


def create_payment_method(app: App, name: str, code: str) -> None:
    if payment_method_exists(app, name):
        return

    button = app.spec.child_window(title="Create a new term of payment",
                                   control_type="Button")
    button.wait("exists enabled", timeout=8)
    button.click_input()
    time.sleep(0.9)

    set_field(app, "Name", name)
    set_field(app, "Description", name)
    payment_code = app.spec.child_window(
        title="!editorPaymentPaymentcode!",
        control_type="ComboBox").wrapper_object()
    select_combo(app, payment_code, code)
    for field in ("Cash discount", "Discount Days", "Net Days"):
        ctrl = app.spec.child_window(title=field,
                                     control_type="Edit").wrapper_object()
        if (val(ctrl) or "").strip() not in ("0", "0%"):
            set_text(app, ctrl, "0")

    app.spec.child_window(title="Save the current contents",
                          control_type="Button").click_input()
    time.sleep(0.9)
