from fk import *


def main():
    start_log("open_new_product")
    spec, w = get_app()
    navs = [t for t in w.descendants(control_type="Text")
            if (t.window_text() or "").strip() == "New product"]
    navs.sort(key=lambda t: t.rectangle().left)
    if not navs:
        log("New product nav not found")
        return
    click(navs[0])
    time.sleep(2.0)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    log("edit names:",
        [(e.element_info.name, e.rectangle()) for e in w.descendants(control_type="Edit")])
    log("combo names:",
        [(c.element_info.name, c.rectangle()) for c in w.descendants(control_type="ComboBox")])
    snap(w, "new_product_open")


run(main)
