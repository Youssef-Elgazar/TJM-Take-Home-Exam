from fk import *


def main():
    start_log("maximize_editor")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").lstrip("*") == "New Order"]
    if tabs:
        click(tabs[0])
        time.sleep(0.9)

    log("grid before:", grid_rect(spec, w))
    btns = [b for b in w.descendants(control_type="Button")
            if (b.window_text() or "").strip() in ("Minimize", "Maximize", "Restore")
            and b.rectangle().left > 1700
            and 120 <= b.rectangle().top <= 190]
    btns.sort(key=lambda b: b.rectangle().left)
    log("editor buttons:", [(b.window_text(), b.rectangle()) for b in btns])
    if len(btns) >= 2:
        click(btns[1])
        log("clicked:", btns[1].window_text())
        time.sleep(1.2)
    log("grid after:", grid_rect(spec, w))

    try:
        lr = label(spec, "Remarks").rectangle()
        log("Remarks label:", lr)
        imgs = [i for i in w.descendants(control_type="Image")
                if abs(i.rectangle().top - lr.top) <= 35
                and abs(i.rectangle().left - lr.right) <= 45]
        log("images near Remarks:", [i.rectangle() for i in imgs])
    except Exception as exc:
        log("Remarks lookup failed:", repr(exc))
    snap(w, "maximize_editor")


run(main)
