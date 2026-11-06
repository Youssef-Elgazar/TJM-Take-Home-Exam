from fk import *


def main():
    start_log("close_new_order")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").lstrip("*") == "New Order"]
    if not tabs:
        log("no New Order tab")
        return
    click(tabs[0])
    time.sleep(0.6)
    log("ctrl+f4:", keys(w, "^{F4}"))
    time.sleep(1.5)
    for win in Desktop(backend="uia").windows(process=w.process_id()):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log("dialog:", repr(title), win.element_info.class_name)
        for cb in win.descendants(control_type="CheckBox"):
            log("  checkbox:", repr(cb.window_text()))
        for b in win.descendants(control_type="Button"):
            log("  button:", repr(b.window_text()))
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
