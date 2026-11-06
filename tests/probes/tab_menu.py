from fk import *


def main():
    start_log("tab_menu")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").lstrip("*") == "New Order"]
    if not tabs:
        log("no New Order tab")
        return
    x, y = center(tabs[0])
    log("right-clicking tab at", (x, y))
    mouse.right_click(coords=(x, y))
    time.sleep(0.8)
    items = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").strip()]
    log("main-window menu items:",
        [m.window_text() for m in items])
    for win in Desktop(backend="uia").windows(process=w.process_id()):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log("popup:", repr(title), win.element_info.class_name)
        for m in win.descendants(control_type="MenuItem"):
            log("  item:", repr(m.window_text()))
    snap(w, "tab_menu")


run(main)
