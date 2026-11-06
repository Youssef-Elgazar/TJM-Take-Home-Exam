from fk import *


def main():
    start_log("check_payment")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").strip() == "Bank Transfer"]
    if tabs:
        click(tabs[0])
        time.sleep(0.8)
        for name in ("Name", "Description", "Cash discount",
                     "Discount Days", "Net Days"):
            ctrl = spec.child_window(title=name,
                                     control_type="Edit").wrapper_object()
            log(name, repr(val(ctrl)))
        combo = spec.child_window(title="!editorPaymentPaymentcode!",
                                  control_type="ComboBox").wrapper_object()
        log("code:", repr(combo.selected_text()))
    navs = [t for t in w.descendants(control_type="Text")
            if (t.window_text() or "").strip() == "terms of payment"]
    navs.sort(key=lambda t: t.rectangle().left)
    click(navs[0])
    time.sleep(1.2)
    log("edits:", [(e.rectangle(), repr(val(e))) for e in
                   w.descendants(control_type="Edit")])
    snap(w, "check_payment")


run(main)
