from fk import *


def refs(w):
    return [e for e in w.descendants(control_type="Edit")
            if (e.element_info.name or "") == "Cust.Ref."]


def main():
    start_log("cust_ref")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").lstrip("*") == "New Order"]
    if tabs:
        click(tabs[0])
        time.sleep(0.9)

    found = refs(w)
    log("Cust.Ref. edits:", [(r.rectangle(), repr(val(r))) for r in found])
    if not found:
        return
    ref = found[0]
    click(ref)
    time.sleep(0.4)
    log("foreground after click:", user32.GetForegroundWindow(),
        "target:", w.handle, "match:", user32.GetForegroundWindow() == w.handle)
    log("value before:", repr(val(ref)))
    log("^a:", keys(w, "^a"))
    log("text:", keys(w, "TEST-REF"))
    log("tab:", keys(w, "{TAB}"))
    time.sleep(0.4)
    found = refs(w)
    log("after:", [(r.rectangle(), repr(val(r))) for r in found])
    snap(w, "cust_ref_probe")


run(main)
