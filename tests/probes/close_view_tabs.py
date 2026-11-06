from fk import *


def menu_item(w, title):
    for item in w.descendants(control_type="MenuItem"):
        if (item.window_text() or "").split("\t")[0].strip() == title:
            return item
    return None


def main():
    start_log("close_view_tabs")
    spec, w = get_app()
    for name in ("VATs", "terms of payment"):
        tabs = [t for t in w.descendants(control_type="TabItem")
                if (t.window_text() or "").strip() == name]
        if not tabs:
            continue
        x, y = center(tabs[0])
        log("middle-click", name)
        mouse.click(button="middle", coords=(x, y))
        time.sleep(1.0)
        if not [t for t in w.descendants(control_type="TabItem")
                if (t.window_text() or "").strip() == name]:
            log("closed", name)
            continue
        log("right-click", name)
        mouse.right_click(coords=(x, y))
        time.sleep(0.8)
        log("menu:", [m.window_text() for m in w.descendants(control_type="MenuItem")])
        close = menu_item(w, "Close")
        if close:
            click(close)
            time.sleep(1.0)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
