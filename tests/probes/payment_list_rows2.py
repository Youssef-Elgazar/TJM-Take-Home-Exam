from fk import *


def main():
    start_log("payment_list_rows2")
    spec, w = get_app()

    best = None
    for pane in w.descendants(control_type="Pane"):
        r = pane.rectangle()
        if r.width() > 800 and r.height() > 150 and r.top >= 600:
            if best is None or (r.width() * r.height()
                                > best.rectangle().width() * best.rectangle().height()):
                best = pane
    if best is None:
        log("no bottom list pane")
        return
    pr = best.rectangle()
    log("pane:", pr)

    mouse.click(button="left", coords=(pr.left + 150, pr.top + 18))
    time.sleep(0.4)
    previous = None
    for index in range(5):
        clip_clear()
        keys(w, "^c")
        time.sleep(0.3)
        text = clip_get()
        if not text or text == previous:
            break
        log(f"row {index}:", repr(text))
        previous = text
        keys(w, "{DOWN}")
        time.sleep(0.2)
    snap(w, "payment_list_rows2")


run(main)
