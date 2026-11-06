from fk import *


def main():
    start_log("close_active_dump")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").strip() == "*New Debtor"]
    if tabs:
        click(tabs[0])
        time.sleep(0.8)
    log("Ctrl+W:", keys(w, "^w"))
    time.sleep(1.5)

    log("windows (descendants):")
    for win in w.descendants(control_type="Window"):
        log("  window:", repr(win.window_text()), win.element_info.class_name,
            win.rectangle())
        for box in win.descendants(control_type="CheckBox"):
            log("    cb:", repr(box.window_text()), box.rectangle(),
                box.get_toggle_state())
        for button in win.descendants(control_type="Button"):
            log("    btn:", repr(button.window_text()), button.rectangle())

    log("top-level windows:")
    for win in Desktop(backend="uia").windows(process=w.process_id()):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log("  window:", repr(title), win.element_info.class_name)
        for box in win.descendants(control_type="CheckBox"):
            log("    cb:", repr(box.window_text()), box.rectangle(),
                box.get_toggle_state())
        for button in win.descendants(control_type="Button"):
            log("    btn:", repr(button.window_text()), button.rectangle())
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    snap(w, "close_active_dump")


run(main)
