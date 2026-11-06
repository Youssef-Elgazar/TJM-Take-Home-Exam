from fk import *


def main():
    start_log("discard_save_parts")
    spec, w = get_app()
    dialogs = [d for d in w.descendants(control_type="Window")
               if (d.window_text() or "").strip() == "Save Parts"]
    if not dialogs:
        log("no Save Parts dialog")
        return
    dialog = dialogs[0]
    items = list(dialog.descendants(control_type="ListItem"))
    log("items:", [(item.window_text(), item.rectangle()) for item in items])
    for item in items:
        rect = item.rectangle()
        mouse.click(button="left", coords=(rect.left + 12,
                                           (rect.top + rect.bottom) // 2))
        time.sleep(0.3)
    for button in dialog.descendants(control_type="Button"):
        if (button.window_text() or "").strip() == "OK":
            click(button)
            log("clicked OK")
            time.sleep(1.2)
            break
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    snap(w, "discard_save_parts")


run(main)
