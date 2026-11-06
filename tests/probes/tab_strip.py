from fk import *


def main():
    start_log("tab_strip")
    spec, w = get_app()
    log("controls in the tab strip:")
    for c in w.descendants():
        r = c.rectangle()
        if 110 <= r.top <= 170 and 380 <= r.left <= 900:
            log(c.element_info.control_type, "|", repr(c.window_text()),
                "|", r, "|", c.element_info.class_name)
    snap(w, "tab_strip")


run(main)
