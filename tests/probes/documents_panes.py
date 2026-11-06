from fk import *


def main():
    start_log("documents_panes")
    spec, w = get_app()
    navs = [t for t in w.descendants(control_type="Text")
            if (t.window_text() or "").strip() == "Documents"]
    navs.sort(key=lambda t: t.rectangle().left)
    if navs:
        click(navs[0])
        time.sleep(1.5)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    for pane in w.descendants(control_type="Pane"):
        r = pane.rectangle()
        if r.width() > 700 and r.height() > 400:
            log("pane:", repr(pane.window_text()), r)
    snap(w, "documents_panes")


run(main)
