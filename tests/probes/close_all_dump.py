from fk import *


def main():
    start_log("close_all_dump")
    spec, w = get_app()
    files = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").split("\t")[0].strip() == "File"]
    click(files[0])
    time.sleep(0.8)
    close_all = [m for m in w.descendants(control_type="MenuItem")
                 if (m.window_text() or "").split("\t")[0].strip() == "Close All"]
    if not close_all:
        log("no Close All")
        return
    click(close_all[0])
    time.sleep(1.5)

    log("top-level windows:")
    for win in Desktop(backend="uia").windows(process=w.process_id()):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log(" window:", repr(title), win.element_info.class_name, win.rectangle())
        for box in win.descendants(control_type="CheckBox"):
            log("  cb:", repr(box.window_text()), box.rectangle(),
                box.get_toggle_state())
        for button in win.descendants(control_type="Button"):
            log("  btn:", repr(button.window_text()), button.rectangle())

    log("main checkboxes:")
    for box in w.descendants(control_type="CheckBox"):
        log("  cb:", repr(box.window_text()), box.rectangle(),
            box.get_toggle_state())
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    snap(w, "close_all_dump")


run(main)
