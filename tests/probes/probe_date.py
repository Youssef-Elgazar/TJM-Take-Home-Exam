from fk import *


def row_edits(spec, w, label_text):
    lr = label(spec, label_text).rectangle()
    es = [e for e in w.descendants(control_type="Edit")
          if abs(e.rectangle().top - lr.top) <= 10]
    return sorted(es, key=lambda e: e.rectangle().left)


def main():
    start_log("date_probe")
    log("script started")
    spec, w = get_app()
    spec.child_window(title="Create: New Order", control_type="Button").click_input()
    time.sleep(2.0)

    no_edit, date_edit = row_edits(spec, w, "Date")[:2]
    log("default date:", repr(val(date_edit)))
    r = date_edit.rectangle()
    ymid = (r.top + r.bottom) // 2

    log("\n[1] set_edit_text formats")
    for text in ["14 Jul 2026", "2026-07-14", "14/07/2026", "14.07.2026"]:
        click(date_edit)
        date_edit.set_edit_text(text)
        keys(w, "{TAB}")
        time.sleep(0.5)
        log(f"   set {text!r} -> {val(date_edit)!r}")

    log("\n[2] keystrokes after Ctrl+A")
    click(date_edit)
    keys(w, "^a")
    keys(w, "14 Jul 2026")
    time.sleep(0.4)
    log("   typed ->", repr(val(date_edit)))

    log("\n[3] UP/DOWN on each segment")
    for dx in range(3, r.width() - 6, 8):
        mouse.click(button="left", coords=(r.left + dx, ymid))
        time.sleep(0.15)
        before = val(date_edit)
        keys(w, "{UP}")
        time.sleep(0.15)
        after = val(date_edit)
        keys(w, "{DOWN}")
        time.sleep(0.15)
        log(f"   dx={dx:3d}: {before!r} -> {after!r}")

    snap(w, "date_calendar")
    log("\nDone. Close the order tab WITHOUT saving.")


run(main)
