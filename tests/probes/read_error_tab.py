from fk import *


def main():
    start_log("read_error_tab")
    spec, w = get_app()
    err = [t for t in w.descendants(control_type="TabItem")
           if (t.window_text() or "").strip() == "Error"]
    if not err:
        log("no Error tab")
        return
    click(err[0])
    time.sleep(0.8)
    for edit in w.descendants(control_type="Edit"):
        value = val(edit)
        if value:
            log(repr(value[:3000]))


run(main)
