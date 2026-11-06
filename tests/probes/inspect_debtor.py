from fk import *


def main():
    start_log("inspect_debtor")
    spec, w = get_app()
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    for tab in w.descendants(control_type="TabItem"):
        title = (tab.window_text() or "").strip()
        if "Debtor" in title or "Northstar" in title:
            click(tab)
            time.sleep(0.9)
            log("debtor tab:", repr(title))
            for name in ("Customer ID", "Company", "Alias name"):
                try:
                    ctrl = spec.child_window(title=name,
                                             control_type="Edit").wrapper_object()
                    log(" ", name, repr(val(ctrl)))
                except Exception as exc:
                    log(" ", name, "error", repr(exc))
            save = spec.child_window(title="Save the current contents",
                                     control_type="Button")
            log("  Save enabled:", save.is_enabled())
            break
    snap(w, "inspect_debtor")


run(main)
