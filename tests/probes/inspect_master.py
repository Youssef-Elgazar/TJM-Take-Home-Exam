"""Read-only check of which debtors/products already exist (spine prerequisite)."""
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


def main():
    start_log("inspect_master")
    log("script started")
    spec, w = get_app()

    spec.child_window(title="Create: New Order",
                      control_type="Button").click_input()
    time.sleep(2.0)
    snap(w, "inspect_0_new_order")

    log("\n[1] debtor search")
    icons = address_icons(spec, w)
    if not icons:
        log("!! no address icons")
        return
    click(icons[0])
    dlg = spec.child_window(title="Select the address", control_type="Window")
    dlg.wait("exists", timeout=8)
    dw = dlg.wrapper_object()
    search = dlg.child_window(control_type="Edit")
    for term in ("Northstar", "MAMarine"):
        search.set_edit_text(term)
        time.sleep(1.5)
        log(f"   {term!r}: dialog open={dlg.exists()}")
        if dlg.exists():
            log("     row:", repr(read_first_row(dlg, dw)))
    dlg.child_window(title="Cancel", control_type="Button").click_input()
    time.sleep(1.0)

    log("\n[2] product search")
    for term in ("CHR-ERG-01", "MAT-DESK-02", "TST-A-01"):
        icons = items_icons(spec, w)
        click(icons[0])
        pd = spec.child_window(title="Select a product", control_type="Window")
        pd.wait("exists", timeout=8)
        edit = pd.child_window(control_type="Edit")
        edit.set_edit_text(term)
        time.sleep(1.5)
        exists = pd.exists()
        log(f"   {term!r}: dialog open={exists}")
        if exists:
            log("     row:", repr(read_first_row(pd, pd.wrapper_object())))
            pd.child_window(title="Cancel", control_type="Button").click_input()
            time.sleep(1.0)
        else:
            log("     auto-selected and closed -> product exists")

    snap(w, "inspect_9_final")
    log("\nDone. The New Order tab is still open; close it WITHOUT saving.")


run(main)
