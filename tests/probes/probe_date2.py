from fk import *

TARGET = (14, "Jul", 2026)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def parse(v):
    parts = v.split()
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), parts[1], int(parts[2])
    except ValueError:
        return None


def changed_part(a, b):
    pa, pb = parse(a), parse(b)
    if not pa or not pb:
        return None
    diffs = [n for n, x, y in zip(("day", "month", "year"), pa, pb) if x != y]
    return diffs[0] if len(diffs) == 1 else None


def date_edit_of(spec, w):
    lr = label(spec, "Date").rectangle()
    for e in w.descendants(control_type="Edit"):
        r = e.rectangle()
        if abs(r.top - lr.top) <= 10 and r.left > lr.right:
            return e
    return None


def main():
    start_log("date_probe2")
    log("script started")
    spec, w = get_app()
    spec.child_window(title="Create: New Order", control_type="Button").click_input()
    time.sleep(2.0)

    de = date_edit_of(spec, w)
    if de is None:
        log("!! date edit not found")
        return
    r = de.rectangle()
    ymid = (r.top + r.bottom) // 2
    log("start:", repr(val(de)), "| rect:", r)

    def read():
        time.sleep(0.25)
        return val(de)

    log("\n[1] segment under each x: click, UP, read, DOWN, read")
    seg_x = {}
    for dx in range(3, r.width() - 6, 4):
        mouse.click(button="left", coords=(r.left + dx, ymid))
        time.sleep(0.2)
        before = read()
        keys(w, "{UP}")
        after = read()
        keys(w, "{DOWN}")
        back = read()
        part = changed_part(before, after)
        note = "" if back == before else "   !! did not restore"
        log(f"   dx={dx:3d}: {before!r} -> {after!r} -> {back!r}  segment={part}{note}")
        if part:
            seg_x.setdefault(part, []).append(dx)

    log("   ranges:", {k: (min(v), max(v)) for k, v in seg_x.items()})
    mid = {k: r.left + (min(v) + max(v)) // 2 for k, v in seg_x.items()}
    if len(mid) < 3:
        log("!! did not find all three segments:", list(mid))

    def seg_click(name):
        mouse.click(button="left", coords=(mid[name], ymid))
        time.sleep(0.25)

    log("\n[2] typing into one segment at a time")
    for name, text in [("year", "2025"), ("year", "2026"), ("month", "Jul"),
                       ("month", "7"), ("day", "14")]:
        if name not in mid:
            continue
        seg_click(name)
        keys(w, text)
        log(f"   typed {text!r} in {name}: {read()!r}")

    log("\n[3] reach", TARGET, "with UP/DOWN steps")

    def step(name, delta):
        if delta == 0 or name not in mid:
            return
        seg_click(name)
        for _ in range(abs(delta)):
            keys(w, "{UP}" if delta > 0 else "{DOWN}")
            time.sleep(0.05)

    for part in ("year", "month", "day"):
        cur = parse(read())
        if cur is None:
            log("!! cannot parse", repr(val(de)))
            return
        if part == "year":
            delta = TARGET[2] - cur[2]
        elif part == "month":
            delta = MONTHS.index(TARGET[1]) - MONTHS.index(cur[1])
        else:
            delta = TARGET[0] - cur[0]
        log(f"   {part}: delta {delta}")
        step(part, delta)
        log("   ->", repr(read()))

    ref = spec.child_window(title="Cust.Ref.", control_type="Edit").wrapper_object()
    click(ref)
    time.sleep(0.6)
    log("   after leaving the field:", repr(read()))
    snap(w, "date2_final")
    log("\nDone. Close the order tab WITHOUT saving.")


run(main)
