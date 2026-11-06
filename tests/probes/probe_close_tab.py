from fk import *


def handle_dialogs(pid):
    acted = False
    for win in Desktop(backend="uia").windows(process=pid):
        title = win.window_text() or ""
        if title.startswith("Fakturama - "):
            continue
        log("dialog:", repr(title), win.element_info.class_name)
        btns = list(win.descendants(control_type="Button"))
        log("  buttons:", [b.window_text() for b in btns])
        for want in ("No", "Don't Save", "Don't save", "Cancel"):
            hit = [b for b in btns
                   if (b.window_text() or "").strip().lower() == want.lower()]
            if hit:
                hit[0].click_input()
                log("  clicked:", want)
                time.sleep(0.8)
                acted = True
                break
    return acted


def main():
    start_log("close_tab2")
    spec, w = get_app()
    pid = w.process_id()

    tabs = [t for t in w.descendants(control_type="TabItem")
            if "New Term of Payment" in (t.window_text() or "")]
    if not tabs:
        log("no target tab")
        return
    tab = tabs[0]
    click(tab)              # a real click brings the window to the foreground
    time.sleep(0.6)
    fg = user32.GetForegroundWindow()
    log("foreground:", fg, "target:", w.handle, "match:", fg == w.handle)

    for seq in ("^{F4}", "^w", "{ESC}"):
        sent = keys(w, seq)
        log(f"sent {seq!r} -> {sent}")
        time.sleep(1.0)
        handle_dialogs(pid)
        now = [t.window_text() for t in w.descendants(control_type="TabItem")]
        log("  tabs:", now)
        if not any("New Term of Payment" in (t or "") for t in now):
            log("tab closed")
            return

    log("tab still open")


run(main)
