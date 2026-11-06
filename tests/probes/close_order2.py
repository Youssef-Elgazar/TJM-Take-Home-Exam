from fk import *


def dialogs(pid):
    out = []
    for win in Desktop(backend="uia").windows(process=pid):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        out.append(win)
    return out


def main():
    start_log("close_order2")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").lstrip("*") == "New Order"]
    if not tabs:
        log("no New Order tab")
        return
    r = tabs[0].rectangle()
    y = (r.top + r.bottom) // 2
    log("tab rect:", r)
    for dx in (-8, -4, 2, 8, 14, 20):
        x = r.right + dx
        mouse.move(coords=(x, y))
        time.sleep(0.4)
        mouse.click(button="left", coords=(x, y))
        time.sleep(1.0)
        found = dialogs(w.process_id())
        if found:
            for d in found:
                log("dialog:", repr(d.window_text()), d.element_info.class_name)
                for cb in d.descendants(control_type="CheckBox"):
                    log("  checkbox:", repr(cb.window_text()))
                for b in d.descendants(control_type="Button"):
                    log("  button:", repr(b.window_text()))
            return
        log(f"dx={dx}: no dialog, tabs=",
            [t.window_text() for t in w.descendants(control_type="TabItem")])
    log("no close control found")


run(main)
