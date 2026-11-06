from fk import *


def main():
    start_log("inspect_order_grid")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").lstrip("*") == "New Order"]
    if tabs:
        click(tabs[0])
        time.sleep(0.9)
    g = grid_rect(spec, w)
    log("grid:", g)
    for row in (1, 2, 3):
        x = g.left + 22
        y = g.top + 31 + 20 * (row - 1)
        mouse.click(button="left", coords=(x, y))
        time.sleep(0.3)
        clip_clear()
        keys(w, "^c")
        time.sleep(0.3)
        log(f"row {row} at y={y}:", repr(clip_get()))
    for name in ("Total Net", "VAT", "Total"):
        ctrl = spec.child_window(title=name,
                                 control_type="Edit").wrapper_object()
        log(name, repr(val(ctrl)))
    snap(w, "inspect_order_grid")


run(main)
