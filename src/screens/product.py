"""New Product creation."""
from __future__ import annotations

import time

from ..extract.schema import product_gross_price
from ..ui.driver import App, click, label, select_combo, set_field, set_text
from .lists import list_contains


def product_exists(app: App, sku: str) -> bool:
    return list_contains(app, "Products", sku)


def _edit_beside(app: App, label_text: str):
    lr = label(app.spec, label_text).rectangle()
    edits = [edit for edit in app.wrapper.descendants(control_type="Edit")
             if abs(edit.rectangle().top - lr.top) <= 12
             and edit.rectangle().left > lr.right]
    edits.sort(key=lambda item: item.rectangle().left)
    return edits[0] if edits else None


def create_product(app: App, item) -> None:
    navs = [tab for tab in app.wrapper.descendants(control_type="Text")
            if (tab.window_text() or "").strip() == "New product"]
    navs.sort(key=lambda item: item.rectangle().left)
    if not navs:
        raise RuntimeError("New product navigation not found")
    click(navs[0])
    time.sleep(2.0)

    set_field(app, "Item Number", item.sku)
    set_field(app, "Name", item.description)
    set_field(app, "Description", item.description)

    price = _edit_beside(app, "Price (gross)")
    if price is None:
        raise RuntimeError("Price (gross) edit not found")
    set_text(app, price,
             f"{product_gross_price(item.unit_net, item.vat_pct):.2f}")

    cost = _edit_beside(app, "cost price (net)")
    if cost is None:
        raise RuntimeError("cost price (net) edit not found")
    set_text(app, cost, "0.00")

    vat = app.spec.child_window(title="VAT",
                                control_type="ComboBox").wrapper_object()
    select_combo(app, vat, f"VAT {int(item.vat_pct)}%")
    set_field(app, "Stock", "0.00")

    app.spec.child_window(title="Save the current contents",
                          control_type="Button").click_input()
    time.sleep(1.2)
