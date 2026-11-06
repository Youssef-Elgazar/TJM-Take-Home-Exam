from fk import *


def main():
    start_log("close_error")
    spec, w = get_app()
    err = [t for t in w.descendants(control_type="TabItem")
           if (t.window_text() or "").strip() == "Error"]
    if not err:
        log("no Error tab")
        return
    click(err[0])
    time.sleep(0.8)
    log("buttons:", [(b.window_text(), b.rectangle())
                     for b in w.descendants(control_type="Button")])
    for button in w.descendants(control_type="Button"):
        if (button.window_text() or "").strip().lower() == "ok":
            click(button)
            time.sleep(0.8)
            break
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
