"""Check existing debtors/products, opening a fresh dialog for each lookup."""
from fk import *


def read_first_row(dlg_spec, dlg_wrapper, x_offset=120):
    search = dlg_spec.child_window(control_type="Edit")
    sr, dr = search.rectangle(), dlg_wrapper.rectangle()
    mouse.click(button="left", coords=(dr.left + x_offset, sr.bottom + 40))
    time.sleep(0.3)
    clip_clear()
    keys(dlg_wrapper, "^c")
    time.sleep(0.3)
    return clip_get()


def debtor_lookup(spec, w, term):
    icons = address_icons(spec, w)
    if not icons:
        return "<no address icons>"
    click(icons[0])
    dlg = spec.child_window(title="Select the address", control_type="Window")
    dlg.wait("exists", timeout=8)
    dw = dlg.wrapper_object()
    dlg.child_window(control_type="Edit").set_edit_text(term)
    time.sleep(1.5)
    row = ""
    try:
        row = read_first_row(dlg, dw)
    except Exception as exc:
        row = f"<read failed: {exc}>"
    if dlg.exists():
        dlg.child_window(title="Cancel", control_type="Button").click_input()
        time.sleep(0.8)
    return row


def product_lookup(spec, w, term):
    icons = items_icons(spec, w)
    if not icons:
        return "<no items icons>"
    click(icons[0])
    dlg = spec.child_window(title="Select a product", control_type="Window")
    dlg.wait("exists", timeout=8)
    dw = dlg.wrapper_object()
    dlg.child_window(control_type="Edit").set_edit_text(term)
    time.sleep(1.5)
    if not dlg.exists():
        return "<auto-selected -> product exists>"
    row = ""
    try:
        row = read_first_row(dlg, dw)
    except Exception as exc:
        row = f"<read failed: {exc}>"
    if dlg.exists():
        dlg.child_window(title="Cancel", control_type="Button").click_input()
        time.sleep(0.8)
    return row


def main():
    start_log("inspect_master2")
    spec, w = get_app()
    spec.child_window(title="Create: New Order",
                      control_type="Button").click_input()
    time.sleep(2.0)

    log("[debtors]")
    for term in ("MAMarine", "Northstar"):
        log(f"  {term!r}:", repr(debtor_lookup(spec, w, term)))

    log("[products]")
    for term in ("TST-A-01", "TST-B-01", "CHR-ERG-01", "MAT-DESK-02"):
        log(f"  {term!r}:", repr(product_lookup(spec, w, term)))

    snap(w, "inspect2_final")
    log("Done. Close the New Order tab WITHOUT saving.")


run(main)
