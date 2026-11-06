from fk import *


def main():
    start_log("verify_documents")
    spec, w = get_app()

    navs = [t for t in w.descendants(control_type="Text")
            if (t.window_text() or "").strip() == "Documents"]
    navs.sort(key=lambda t: t.rectangle().left)
    if not navs:
        log("no Documents nav")
        return
    click(navs[0])
    time.sleep(1.5)
    snap(w, "documents_verify")

    best = None
    for pane in w.descendants(control_type="Pane"):
        r = pane.rectangle()
        if r.width() > 900 and r.height() > 500 and 180 <= r.top <= 260:
            if best is None or (r.width() * r.height()
                                > best.rectangle().width() * best.rectangle().height()):
                best = pane
    if best is None:
        log("documents pane not found")
        return
    pr = best.rectangle()
    log("pane:", pr)

    previous = None
    for index in range(4):
        y = pr.top + 25 + 20 * index
        mouse.click(button="left", coords=(pr.left + 120, y))
        time.sleep(0.3)
        clip_clear()
        keys(w, "^c")
        time.sleep(0.3)
        text = clip_get()
        if not text or text == previous:
            break
        log(f"row {index}:", repr(text))
        previous = text


run(main)
