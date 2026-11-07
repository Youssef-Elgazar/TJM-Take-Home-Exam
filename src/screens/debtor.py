"""New Debtor creation."""
from __future__ import annotations

import time

from ..ui.driver import (App, click, label, select_combo, send_keys_to,
                         set_field, set_text, type_field, val)
from .lists import list_contains


def debtor_exists(app: App, debtor) -> bool:
    """True when this debtor is already listed.

    The Debtors list quick-search keys on a single term (the contact's first
    name), so probe the first name, then the last name, then the company.
    """
    for term in (debtor.contact.first_name, debtor.contact.last_name,
                 debtor.company):
        if term and list_contains(app, "Debtors", term):
            return True
    return False


def _edits_on_row(app: App, label_text: str):
    lr = label(app.spec, label_text).rectangle()
    edits = [edit for edit in app.wrapper.descendants(control_type="Edit")
             if abs(edit.rectangle().top - lr.top) <= 12
             and edit.rectangle().left > lr.right]
    edits.sort(key=lambda item: item.rectangle().left)
    return edits


def _check_role(app: App, role: str) -> None:
    lr = label(app.spec, "address type").rectangle()
    arrows = [button for button in app.wrapper.descendants(control_type="Button")
              if (button.window_text() or "").strip() == ""
              and button.rectangle().left >= lr.right
              and abs(button.rectangle().top - lr.top) <= 15]
    if not arrows:
        raise RuntimeError("address type arrow not found")
    click(arrows[0])
    time.sleep(0.45)

    boxes = [box for box in app.wrapper.descendants(control_type="CheckBox")
             if (box.window_text() or "").strip() == role]
    if not boxes:
        raise RuntimeError(f"role checkbox {role!r} not found")
    if boxes[0].get_toggle_state() != 1:
        click(boxes[0])
        time.sleep(0.2)
    send_keys_to(app, "{ESC}")
    time.sleep(0.15)


def _set_address(app: App, address) -> None:
    set_field(app, "Street", address.street)
    edits = _edits_on_row(app, "ZIP - City")
    if len(edits) < 2:
        raise RuntimeError("ZIP / City edits not found")
    set_text(app, edits[0], address.zip)
    set_text(app, edits[1], address.city)
    country = app.spec.child_window(title="Country",
                                    control_type="ComboBox").wrapper_object()
    select_combo(app, country, address.country)


def create_debtor(app: App, debtor, payment_method: str) -> None:
    navs = [item for item in app.wrapper.descendants(control_type="Text")
            if (item.window_text() or "").strip() == "New Contact"]
    navs.sort(key=lambda item: item.rectangle().left)
    if not navs:
        raise RuntimeError("New Contact navigation not found")
    click(navs[0])
    time.sleep(0.9)

    names = _edits_on_row(app, "First Name Last Name")
    if len(names) < 2:
        raise RuntimeError("First Name / Last Name edits not found")
    type_field(app, "Company", debtor.company, commit=names[0])
    set_text(app, names[0], debtor.contact.first_name)
    set_text(app, names[1], debtor.contact.last_name)

    _set_address(app, debtor.billing)
    set_field(app, "E-Mail", debtor.contact.email)
    set_field(app, "Telephone", debtor.contact.phone)
    _check_role(app, "Invoice address")

    delivery_differs = (
        debtor.delivery.name != debtor.billing.name
        or debtor.delivery.street != debtor.billing.street
        or debtor.delivery.zip != debtor.billing.zip
        or debtor.delivery.city != debtor.billing.city
    )
    if delivery_differs:
        plus = app.spec.child_window(title="+",
                                     control_type="Button").wrapper_object()
        click(plus)
        time.sleep(0.9)
        set_field(app, "additional name", debtor.delivery.name)
        _set_address(app, debtor.delivery)
        _check_role(app, "Delivery address")

    misc = [tab for tab in app.wrapper.descendants(control_type="TabItem")
            if (tab.window_text() or "").strip() == "Miscellaneous"]
    if not misc:
        raise RuntimeError("Miscellaneous tab not found")
    click(misc[0])
    time.sleep(0.4)
    set_field(app, "Alias name", debtor.alias)
    discount = app.spec.child_window(title="Discount",
                                     control_type="Edit").wrapper_object()
    if (val(discount) or "").strip() not in ("0", "0%", ""):
        set_text(app, discount, "0")
    net_gross = app.spec.child_window(title="Net or Gross",
                                      control_type="ComboBox").wrapper_object()
    select_combo(app, net_gross, "Net")
    payment = app.spec.child_window(title="Payment",
                                    control_type="ComboBox").wrapper_object()
    select_combo(app, payment, payment_method)

    app.spec.child_window(title="Save the current contents",
                          control_type="Button").click_input()
    time.sleep(0.9)
