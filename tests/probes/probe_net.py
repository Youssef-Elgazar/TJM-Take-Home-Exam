from fk import *


def mode_combo(spec, w):
    lr = label(spec, "Date").rectangle()
    for c in w.descendants(control_type="ComboBox"):
        r = c.rectangle()
        if abs(r.top - lr.top) <= 10 and r.left > lr.right:
            return c
    return None


def cell(spec, w, row, dx):
    g = grid_rect(spec, w)
    return g.left + 2 + dx, g.top + 31 + 20 * (row - 1)


def read_row(spec, w, row):
    x, y = cell(spec, w, row, 20)
    mouse.click(button="left", coords=(x, y))
    time.sleep(0.3)
    clip_clear()
    keys(w, "^c")
    time.sleep(0.3)
    return clip_get()


def edit_cell(spec, w, row, dx, text):
    x, y = cell(spec, w, row, dx)
    mouse.double_click(button="left", coords=(x, y))
    time.sleep(0.3)
    keys(w, "^a")
    keys(w, text)
    keys(w, "{ENTER}")
    time.sleep(0.4)


def main():
    start_log("net_probe")
    log("script started")
    spec, w = get_app()
    spec.child_window(title="Create: New Order", control_type="Button").click_input()
    time.sleep(2.0)

    mode = mode_combo(spec, w)
    log("price-mode combo:", mode.rectangle() if mode else None)
    if mode:
        mode.select("Net")
        time.sleep(0.5)
        log("   mode ->", repr(mode.selected_text()))

    icons = items_icons(spec, w)
    log("items icons:", [i.rectangle() for i in icons])
    click(icons[0])
    dlg = spec.child_window(title="Select a product", control_type="Window")
    dlg.wait("exists", timeout=8)
    dlg.child_window(control_type="Edit").set_edit_text("TST-B-01")
    time.sleep(1.5)
    log("   product dialog still open:", dlg.exists())

    edit_cell(spec, w, 1, 90, "2")     # Qty
    edit_cell(spec, w, 1, 690, "100")  # U.Price (net)
    edit_cell(spec, w, 1, 790, "10")   # Discount
    log("   row 1:", repr(read_row(spec, w, 1)))
    for name in ("Total Net", "Discount", "VAT", "Total"):
        try:
            ctrl = spec.child_window(title=name, control_type="Edit").wrapper_object()
            log(f"   {name}:", repr(val(ctrl)))
        except Exception as e:
            log(f"   {name} failed:", repr(e))

    snap(w, "net_6_discount")
    log("\nDone. Close the order tab WITHOUT saving.")


run(main)
