from fk import *


def main():
    start_log("file_menu_probe")
    spec, w = get_app()
    files = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").strip() == "File"]
    log("File items:", [m.rectangle() for m in files])
    if not files:
        return
    click(files[0])
    time.sleep(1.0)
    log("main menuitems:",
        [m.window_text() for m in w.descendants(control_type="MenuItem")])
    log("Menu controls:")
    for menu in w.descendants(control_type="Menu"):
        items = [c.window_text() for c in menu.descendants(control_type="MenuItem")]
        log("  menu:", repr(menu.window_text()), menu.rectangle(), items)
    log("other windows:")
    for win in Desktop(backend="uia").windows():
        title = win.window_text() or ""
        cls = win.element_info.class_name
        if cls == "#32768" or (title and "Fakturama" not in title):
            log("  window:", repr(title), cls)
            for item in win.descendants(control_type="MenuItem"):
                log("    item:", repr(item.window_text()))
    keys(w, "{ESC}")
    snap(w, "file_menu_probe")


run(main)
