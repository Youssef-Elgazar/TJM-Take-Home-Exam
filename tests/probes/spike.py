import sys, os
from pywinauto import Desktop

label = sys.argv[1] if len(sys.argv) > 1 else "dump"
os.makedirs("dumps", exist_ok=True)

desktop = Desktop(backend="uia")
main = desktop.window(title_re="^Fakturama - .*")
pid = main.process_id()


def dump_tree(wrapper, f, depth=0, max_depth=25):
    """One line per control."""
    try:
        info = wrapper.element_info
        f.write(
            f"{'  ' * depth}{info.control_type} | name={info.name!r} | "
            f"auto_id={info.automation_id!r} | class={info.class_name!r} | "
            f"rect={info.rectangle}\n"
        )
    except Exception as e:
        f.write(f"{'  ' * depth}<error reading control: {e}>\n")
        return
    if depth >= max_depth:
        return
    try:
        children = wrapper.children()
    except Exception:
        return
    for c in children:
        dump_tree(c, f, depth + 1, max_depth)


for i, w in enumerate(desktop.windows(process=pid)):
    title = w.window_text() or f"untitled{i}"
    safe = "".join(c if c.isalnum() else "_" for c in title)[:40]
    base = f"dumps/{label}_{i}_{safe}"
    print("dumping:", title)

    with open(base + ".txt", "w", encoding="utf-8") as f:
        dump_tree(w, f)

    try:
        desktop.window(handle=w.handle).print_control_identifiers(
            filename=base + "_pywinauto.txt"
        )
    except Exception as e:
        print("  built-in dump failed:", e)

    try:
        w.capture_as_image().save(base + ".png")
    except Exception as e:
        print("  screenshot failed:", e)
