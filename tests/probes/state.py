from fk import *


def main():
    start_log("state_check")
    spec, w = get_app()
    log("foreground:", user32.GetForegroundWindow(), "target:", w.handle,
        "match:", user32.GetForegroundWindow() == w.handle)
    log("force_foreground:", force_foreground(w.handle))
    log("foreground now:", user32.GetForegroundWindow())
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    log("keyboard test (ESC):", keys(w, "{ESC}"))


run(main)
