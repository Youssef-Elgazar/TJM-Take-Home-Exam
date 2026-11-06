from fk import *


def main():
    start_log("inspect_marta")
    spec, w = get_app()
    tabs = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").strip() == "Marta Klein"]
    if not tabs:
        log("no Marta Klein tab")
        log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
        return
    click(tabs[0])
    time.sleep(0.9)

    for name in ("Customer ID", "Company"):
        ctrl = spec.child_window(title=name,
                                 control_type="Edit").wrapper_object()
        log(name, repr(val(ctrl)))
    fl = label(spec, "First Name Last Name").rectangle()
    edits = [e for e in w.descendants(control_type="Edit")
             if abs(e.rectangle().top - fl.top) <= 12
             and e.rectangle().left > fl.right]
    edits.sort(key=lambda e: e.rectangle().left)
    log("names:", [val(e) for e in edits])

    misc = [t for t in w.descendants(control_type="TabItem")
            if (t.window_text() or "").strip() == "Miscellaneous"]
    if misc:
        click(misc[0])
        time.sleep(0.6)
        for name in ("Alias name", "Discount"):
            ctrl = spec.child_window(title=name,
                                     control_type="Edit").wrapper_object()
            log(name, repr(val(ctrl)))
        payment = spec.child_window(title="Payment",
                                    control_type="ComboBox").wrapper_object()
        log("Payment:", repr(payment.selected_text()))
    save = spec.child_window(title="Save the current contents",
                             control_type="Button")
    log("Save enabled:", save.is_enabled())
    snap(w, "inspect_marta")


run(main)
