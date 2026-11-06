from fk import *


def main():
    start_log("inspect_after_fail")
    spec, w = get_app()
    log("tabs:", [t.window_text() for t in w.descendants(control_type="TabItem")])
    log("edits:")
    for edit in w.descendants(control_type="Edit"):
        name = edit.element_info.name or ""
        if name:
            log("  ", repr(name), edit.rectangle())
    log("combos:")
    for combo in w.descendants(control_type="ComboBox"):
        log("  ", repr(combo.element_info.name), combo.rectangle())
    snap(w, "inspect_after_fail")


run(main)
