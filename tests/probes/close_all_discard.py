from fk import *


def dismiss_save_parts(pid):
    for win in Desktop(backend="uia").windows(process=pid):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log("dialog:", repr(title), win.element_info.class_name)
        for box in win.descendants(control_type="CheckBox"):
            state = box.get_toggle_state()
            log("  checkbox:", repr(box.window_text()), state)
            if state == 1:
                box.click_input()
                time.sleep(0.2)
        for button in win.descendants(control_type="Button"):
            if (button.window_text() or "").strip().lower() == "ok":
                button.click_input()
                time.sleep(0.6)
                return True
    return False


def close_all(w):
    files = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").split("\t")[0].strip() == "File"]
    click(files[0])
    time.sleep(0.8)
    items = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").split("\t")[0].strip() == "Close All"]
    if not items:
        keys(w, "{ESC}")
        return
    click(items[0])
    time.sleep(1.2)


def main():
    start_log("close_all_discard")
    spec, w = get_app()
    keys(w, "{ESC}")
    time.sleep(0.3)
    close_all(w)
    dismiss_save_parts(w.process_id())
    time.sleep(0.8)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
