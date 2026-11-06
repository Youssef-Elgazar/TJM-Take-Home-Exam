from fk import *


def main():
    start_log("address_type_popup")
    spec, w = get_app()

    navs = [t for t in w.descendants(control_type="Text")
            if (t.window_text() or "").strip() == "New Contact"]
    navs.sort(key=lambda t: t.rectangle().left)
    if not navs:
        log("New Contact nav not found")
        return
    click(navs[0])
    time.sleep(2.0)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])

    lr = label(spec, "address type").rectangle()
    log("address type label:", lr)
    candidates = []
    for button in w.descendants(control_type="Button"):
        rect = button.rectangle()
        if rect.left >= lr.right and abs(rect.top - lr.top) <= 15:
            candidates.append(button)
    log("arrow candidates:", [(b.rectangle(), b.window_text()) for b in candidates])
    if not candidates:
        return
    click(candidates[0])
    time.sleep(1.0)

    log("checkboxes after click:")
    for box in w.descendants(control_type="CheckBox"):
        log("  ", repr(box.window_text()), box.rectangle())
    log("top-level windows:")
    for win in Desktop(backend="uia").windows(process=w.process_id()):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log("  window:", repr(title), win.element_info.class_name)
        for box in win.descendants(control_type="CheckBox"):
            log("    checkbox:", repr(box.window_text()), box.rectangle())
    snap(w, "address_type_popup")


run(main)
