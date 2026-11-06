from fk import *


def handle_save_parts(w):
    for dialog in w.descendants(control_type="Window"):
        if (dialog.window_text() or "").strip() != "Save Parts":
            continue
        for item in dialog.descendants(control_type="ListItem"):
            rect = item.rectangle()
            mouse.click(button="left", coords=(rect.left + 12,
                                               (rect.top + rect.bottom) // 2))
            time.sleep(0.3)
        for button in dialog.descendants(control_type="Button"):
            if (button.window_text() or "").strip() == "OK":
                click(button)
                time.sleep(1.0)
                return True
    return False


def main():
    start_log("discard_all")
    spec, w = get_app()
    files = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").split("\t")[0].strip() == "File"]
    click(files[0])
    time.sleep(0.8)
    close_all = [m for m in w.descendants(control_type="MenuItem")
                 if (m.window_text() or "").split("\t")[0].strip() == "Close All"]
    if close_all:
        click(close_all[0])
        time.sleep(1.5)
    handle_save_parts(w)
    time.sleep(0.8)

    # View tabs (e.g. Error) close on middle-click.
    for name in ("Error", "Documents", "terms of payment"):
        tabs = [t for t in w.descendants(control_type="TabItem")
                if (t.window_text() or "").strip() == name]
        for tab in tabs:
            mouse.click(button="middle", coords=center(tab))
            time.sleep(0.6)

    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
