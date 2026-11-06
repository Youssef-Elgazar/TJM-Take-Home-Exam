from fk import *


def menu_item(w, title):
    for item in w.descendants(control_type="MenuItem"):
        text = (item.window_text() or "").split("\t")[0].strip()
        if text == title:
            return item
    return None


def close_active(w):
    click(menu_item(w, "File"))
    time.sleep(0.8)
    close = menu_item(w, "Close")
    if close:
        click(close)
        time.sleep(1.0)


def main():
    start_log("close_extra_tabs")
    spec, w = get_app()
    for name in ("VATs", "terms of payment"):
        tabs = [t for t in w.descendants(control_type="TabItem")
                if (t.window_text() or "").strip() == name]
        if tabs:
            log("closing", name)
            click(tabs[0])
            time.sleep(0.6)
            close_active(w)
    docs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").strip() == "Documents"]
    if docs:
        click(docs[0])
        time.sleep(0.6)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
