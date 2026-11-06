from fk import *


def main():
    start_log("close_all_probe")
    spec, w = get_app()
    files = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").strip() == "File"]
    log("File items:", [m.rectangle() for m in files])
    if files:
        click(files[0])
        time.sleep(1.0)
    log("menu items:",
        [m.window_text() for m in w.descendants(control_type="MenuItem")])
    for menu in w.descendants(control_type="Menu"):
        log("menu:", repr(menu.window_text()),
            [c.window_text() for c in menu.descendants(control_type="MenuItem")])
    close_all = [m for m in w.descendants(control_type="MenuItem")
                 if (m.window_text() or "").strip() == "Close All"]
    if close_all:
        log("clicking Close All")
        click(close_all[0])
        time.sleep(1.5)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    snap(w, "close_all_probe")


run(main)
