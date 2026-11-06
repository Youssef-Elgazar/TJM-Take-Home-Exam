from fk import *


def row_edits(spec, w, label_text):
    lr = label(spec, label_text).rectangle()
    es = [e for e in w.descendants(control_type="Edit")
          if abs(e.rectangle().top - lr.top) <= 10]
    return sorted(es, key=lambda e: e.rectangle().left)


def main():
    start_log("header_probe")
    log("script started")
    spec, w = get_app()

    spec.child_window(title="Create: New Order", control_type="Button").click_input()
    time.sleep(2.0)
    snap(w, "hdr_0_new_order")

    no_edit, date_edit = row_edits(spec, w, "Date")[:2]
    log("proposed No.:", repr(val(no_edit)))
    log("default date:", repr(val(date_edit)))

    log("\n[1] date formats")
    for text in ["14 Jul 2026", "2026-07-14", "14/07/2026", "14.07.2026"]:
        click(date_edit)
        date_edit.set_edit_text(text)
        keys(w, "{TAB}")
        time.sleep(0.5)
        log(f"   typed {text!r} -> shows {val(date_edit)!r}")
    click(date_edit)
    date_edit.set_edit_text("14 Jul 2026")
    keys(w, "{TAB}")
    time.sleep(0.4)
    log("   final date:", repr(val(date_edit)))

    log("\n[2] Cust.Ref.")
    ref = spec.child_window(title="Cust.Ref.", control_type="Edit")
    ref.set_edit_text("WEB-2026-0714-A17")
    time.sleep(0.3)
    log("   Cust.Ref. ->", repr(ref.get_value()))
    save = spec.child_window(title="Save the current contents", control_type="Button")
    log("   Save enabled:", save.is_enabled())

    log("\n[3] select an existing debtor")
    icons = address_icons(spec, w)
    log("   address icons:", [i.rectangle() for i in icons])
    if not icons:
        log("   !! no address icons found")
        return
    click(icons[0])
    dlg = spec.child_window(title="Select the address", control_type="Window")
    dlg.wait("exists", timeout=8)
    dw = dlg.wrapper_object()
    search = dlg.child_window(control_type="Edit")
    search.set_edit_text("Elgazar")
    time.sleep(1.5)
    log("   dialog still open after 1-row search:", dlg.exists())
    if dlg.exists():
        sr, dr = search.rectangle(), dw.rectangle()
        mouse.click(button="left", coords=(dr.left + 100, sr.bottom + 40))
        time.sleep(0.3)
        clip_clear()
        keys(dw, "^c")
        time.sleep(0.3)
        log("   row:", repr(clip_get()[:200]))
        dlg.child_window(title="OK", control_type="Button").click_input()
        time.sleep(1.2)

    snap(w, "hdr_1_after_debtor")
    lr = label(spec, "Addresses").rectangle()
    addr = [e for e in w.descendants(control_type="Edit")
            if e.rectangle().left > lr.right
            and lr.top <= e.rectangle().top <= lr.bottom + 30
            and e.rectangle().height() > 30]
    if addr:
        log("   Invoice address ->", repr(val(addr[0])))
    else:
        log("   !! address box not found")

    log("\nDone. Close the order tab WITHOUT saving.")


run(main)
