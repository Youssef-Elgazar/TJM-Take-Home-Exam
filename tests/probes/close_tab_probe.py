from fk import *


def near(items, tab_rect, pad=60):
    out = []
    for item in items:
        r = item.rectangle()
        if (tab_rect.top - 8 <= r.top <= tab_rect.bottom + 8
                and tab_rect.left - pad <= r.left <= tab_rect.right + pad):
            out.append((r, item))
    return out


def main():
    start_log("close_tab_probe")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").strip() == "INV000001"]
    if not tabs:
        log("no INV000001 tab; tabs:",
            [t.window_text() for t in w.descendants(control_type="TabItem")])
        return
    tab = tabs[0]
    r = tab.rectangle()
    y = (r.top + r.bottom) // 2
    mouse.move(coords=((r.left + r.right) // 2, y))
    time.sleep(1.0)
    log("tab rect:", r)
    log("images near tab:")
    for ir, item in near(w.descendants(control_type="Image"), r):
        log("  image:", ir, repr(item.element_info.name))
    log("buttons near tab:")
    for br, item in near(w.descendants(control_type="Button"), r):
        log("  button:", br, repr(item.window_text()))
    snap(w, "close_tab_probe")


run(main)
