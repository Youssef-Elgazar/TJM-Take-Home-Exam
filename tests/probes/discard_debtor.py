from fk import *


def handle_save_parts(w):
    dialogs = [d for d in w.descendants(control_type="Window")
               if (d.window_text() or "").strip() == "Save Parts"]
    for dialog in dialogs:
        items = list(dialog.descendants(control_type="ListItem"))
        log("save-parts items:", [item.window_text() for item in items])
        for item in items:
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
    start_log("discard_debtor")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").strip() == "*New Debtor"]
    if tabs:
        click(tabs[0])
        time.sleep(0.8)
    files = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").split("\t")[0].strip() == "File"]
    click(files[0])
    time.sleep(0.8)
    close = [m for m in w.descendants(control_type="MenuItem")
             if (m.window_text() or "").split("\t")[0].strip() == "Close"]
    if close:
        click(close[0])
        time.sleep(1.2)
    handle_save_parts(w)
    time.sleep(0.8)
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])


run(main)
