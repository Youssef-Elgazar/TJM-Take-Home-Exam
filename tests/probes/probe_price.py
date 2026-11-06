from fk import *
from probe_net import mode_combo, cell, read_row, edit_cell


def add_product(spec, w, sku):
    icons = items_icons(spec, w)
    click(icons[0])
    dlg = spec.child_window(title="Select a product", control_type="Window")
    dlg.wait("exists", timeout=8)
    dlg.child_window(control_type="Edit").set_edit_text(sku)
    time.sleep(1.5)
    return dlg.exists()


def main():
    start_log("price_probe")
    log("script started")
    spec, w = get_app()
    spec.child_window(title="Create: New Order", control_type="Button").click_input()
    time.sleep(2.0)

    mode = mode_combo(spec, w)
    if mode:
        mode.select("Net")
        time.sleep(0.5)

    add_product(spec, w, "TST-A-01")
    edit_cell(spec, w, 1, 690, "90")
    log("   U.Price 90 ->", repr(read_row(spec, w, 1)))
    snap(w, "price_2_uprice90")
    edit_cell(spec, w, 1, 690, "100")
    log("   U.Price 100 ->", repr(read_row(spec, w, 1)))
    snap(w, "price_3_uprice100")

    add_product(spec, w, "tst-c-01")
    log("   two lines:", repr(read_row(spec, w, 1)), "|", repr(read_row(spec, w, 2)))
    edit_cell(spec, w, 2, 90, "3")
    log("   row 2 qty:", repr(read_row(spec, w, 2)))
    snap(w, "price_5_qty_row2")

    icons = items_icons(spec, w)
    x, y = cell(spec, w, 2, 20)
    mouse.click(button="left", coords=(x, y))
    time.sleep(0.3)
    click(icons[2])  # red x removes the selected line
    time.sleep(0.5)
    log("   after removing row 2, row 1:", repr(read_row(spec, w, 1)))
    snap(w, "price_6_after_remove")
    log("\nDone. Close the order tab WITHOUT saving.")


run(main)
