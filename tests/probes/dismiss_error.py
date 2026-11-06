from fk import *


def main():
    start_log("dismiss_error")
    spec, w = get_app()
    found = False
    for dialog in w.descendants(control_type="Window"):
        if (dialog.window_text() or "").strip() == "Internal Error":
            log("dialog:", dialog.rectangle())
            for button in dialog.descendants(control_type="Button"):
                if (button.window_text() or "").strip() == "OK":
                    click(button)
                    log("clicked OK")
                    time.sleep(0.6)
                    found = True
                    break
    if not found:
        log("no Internal Error dialog")
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
