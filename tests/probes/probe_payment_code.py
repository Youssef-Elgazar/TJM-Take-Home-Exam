from fk import *


def texts_named(w, name):
    return [t for t in w.descendants(control_type="Text")
            if (t.window_text() or "").strip() == name]


def click_nav(w, name):
    cands = texts_named(w, name)
    cands.sort(key=lambda t: t.rectangle().left)
    if not cands:
        log("!! nav item not found:", name)
        return False
    log("nav candidates (left, top):",
        [(c.rectangle().left, c.rectangle().top) for c in cands])
    click(cands[0])
    time.sleep(1.5)
    return True


def dump_tabs(w):
    try:
        tabs = [t.window_text() for t in w.descendants(control_type="TabItem")]
        log("tabs:", tabs)
    except Exception as e:
        log("tab dump failed:", repr(e))


def describe_combo(win, title, combo):
    log("")
    log("=== combo:", title, "===")
    r = combo.rectangle()
    log("rect:", r,
        "| class:", combo.element_info.class_name,
        "| type:", combo.element_info.control_type)

    for meth in ("item_texts", "selected_text", "get_value", "texts"):
        try:
            fn = getattr(combo, meth)
            log(f"{meth}():", fn())
        except Exception as e:
            log(f"{meth}() failed:", type(e).__name__, str(e)[:140])

    opened = False
    try:
        combo.expand()
        time.sleep(0.8)
        opened = True
        log("opened via expand()")
    except Exception as e:
        log("expand() failed:", type(e).__name__, str(e)[:140])

    if not opened:
        try:
            combo.click_input()
            time.sleep(0.8)
            opened = True
            log("opened via click_input()")
        except Exception as e:
            log("click_input() failed:", type(e).__name__, str(e)[:140])

    safe = "".join(c if c.isalnum() else "_" for c in title)
    snap(win, "paycode_combo_" + safe)

    # Enumerate any list-like controls that are now visible.
    for ct in ("ListItem", "List", "MenuItem", "TreeItem"):
        try:
            found = [c for c in win.descendants(control_type=ct)
                     if (c.window_text() or "").strip()]
            for c in found:
                log(f"  {ct}:", repr(c.window_text()), c.rectangle())
        except Exception as e:
            log(f"  enumerate {ct} failed:", repr(e))

    # Dump every control that sits in the popup region just below the combo.
    try:
        region = []
        for c in win.descendants():
            rr = c.rectangle()
            if (rr.top >= r.bottom - 4 and rr.top <= r.bottom + 420
                    and r.left - 60 <= rr.left <= r.right + 60):
                region.append((rr.top, rr.left, c.element_info.control_type,
                               c.window_text()))
        region.sort()
        for row in region[:60]:
            log("  region:", row)
    except Exception as e:
        log("  region scan failed:", repr(e))

    try:
        keys(win, "{ESC}")
        time.sleep(0.3)
    except Exception:
        pass


def main():
    start_log("payment_code_probe")
    log("script started")
    spec, w = get_app()
    dump_tabs(w)

    log("\n[1] navigate to terms of payment")
    if not click_nav(w, "terms of payment"):
        return
    snap(w, "paycode_0_terms")

    log("\n[2] open a new term of payment editor")
    try:
        btn = spec.child_window(title="Create a new term of payment",
                                control_type="Button")
        btn.wait("exists enabled", timeout=8)
        btn.click_input()
    except Exception as e:
        log("!! could not click create:", repr(e))
        dump_tabs(w)
        return
    time.sleep(1.5)
    dump_tabs(w)
    snap(w, "paycode_1_editor")

    log("\n[3] read the payment-code combo")
    try:
        pc = spec.child_window(title="!editorPaymentPaymentcode!",
                               control_type="ComboBox").wrapper_object()
        describe_combo(w, "paymentcode", pc)
    except Exception as e:
        log("!! payment-code combo not found:", repr(e))
        try:
            for c in w.descendants(control_type="ComboBox"):
                log("  combo present:", repr(c.window_text()), c.rectangle())
        except Exception as e2:
            log("combo dump failed:", repr(e2))

    log("\n[4] read the Account combo (for reference)")
    try:
        ac = spec.child_window(title="Account",
                               control_type="ComboBox").wrapper_object()
        describe_combo(w, "account", ac)
    except Exception as e:
        log("!! account combo not found:", repr(e))

    snap(w, "paycode_2_final")
    log("\nDone. A blank 'New Term of Payment' tab may be open; "
        "close it WITHOUT saving.")


run(main)
