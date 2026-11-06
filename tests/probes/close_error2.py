from fk import *


def main():
    start_log("close_error2")
    spec, w = get_app()
    err = [t for t in w.descendants(control_type="TabItem")
           if (t.window_text() or "").strip() == "Error"]
    if err:
        click(err[0])
        time.sleep(0.8)
    log("top-level windows:")
    for win in Desktop(backend="uia").windows(process=w.process_id()):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log(" window:", repr(title), win.element_info.class_name, win.rectangle())
        for button in win.descendants(control_type="Button"):
            log("   button:", repr(button.window_text()), button.rectangle())
    log("press ENTER")
    keys(w, "{ENTER}")
    time.sleep(1.0)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
