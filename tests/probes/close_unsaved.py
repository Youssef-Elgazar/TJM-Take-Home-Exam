"""Read the Error tab text and dump the close-unsaved dialog, if any."""
from fk import *


def main():
    start_log("close_unsaved")
    spec, w = get_app()

    err = [t for t in w.descendants(control_type="TabItem")
           if (t.window_text() or "").strip() == "Error"]
    if err:
        click(err[0])
        time.sleep(1.0)
        log("[Error tab edits]")
        for e in w.descendants(control_type="Edit"):
            v = val(e)
            if v:
                log(repr(v[:1200]))
        snap(w, "error_tab")

    new_order = [t for t in w.descendants(control_type="TabItem")
                 if (t.window_text() or "").strip() in ("New Order", "*New Order")]
    if new_order:
        click(new_order[0])
        time.sleep(0.8)

    sent = keys(w, "^{F4}")
    log("\nCtrl+F4 sent:", sent)
    time.sleep(1.5)

    log("\n[top-level windows]")
    for win in Desktop(backend="uia").windows(process=w.process_id()):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log("window:", repr(title), win.element_info.class_name)
        for cb in win.descendants(control_type="CheckBox"):
            log("  checkbox:", repr(cb.window_text()))
        for b in win.descendants(control_type="Button"):
            log("  button:", repr(b.window_text()))

    log("tabs now:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    snap(w, "close_unsaved")


run(main)
