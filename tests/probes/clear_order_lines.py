from fk import *


def main():
    start_log("clear_order_lines")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").lstrip("*") == "New Order"]
    if not tabs:
        log("no New Order tab")
        return
    click(tabs[0])
    time.sleep(0.9)

    grid = grid_rect(spec, w)
    log("grid:", grid)
    x, y = grid.left + 22, grid.top + 31
    mouse.click(button="left", coords=(x, y))
    time.sleep(0.3)
    icons = items_icons(spec, w)
    log("items icons:", [i.rectangle() for i in icons])
    click(icons[2])  # red x removes the selected line
    time.sleep(0.6)

    for name in ("Total Net", "VAT", "Total"):
        try:
            ctrl = spec.child_window(title=name,
                                     control_type="Edit").wrapper_object()
            log(name, repr(val(ctrl)))
        except Exception as exc:
            log(name, "read failed:", repr(exc))
    snap(w, "cleared_order")


run(main)
