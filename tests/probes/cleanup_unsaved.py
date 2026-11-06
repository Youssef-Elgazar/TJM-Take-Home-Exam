import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pywinauto import Desktop, mouse
from src.ui.driver import get_app, center


def dismiss_no(app):
    for win in Desktop(backend="uia").windows(process=app.pid):
        title = (win.window_text() or "").strip()
        if not title or title.startswith("Fakturama - "):
            continue
        for b in win.descendants(control_type="Button"):
            t = (b.window_text() or "").strip().lower()
            if t in ("no", "discard", "don't save", "do not save", "abandon",
                     "close without saving"):
                b.click_input()
                time.sleep(0.6)
                return True
    return False


def main():
    app = get_app()
    target = [t for t in app.wrapper.descendants(control_type="TabItem")
              if (t.window_text() or "").strip() == "*New product"]
    if not target:
        print("no unsaved product tab")
        return
    mouse.click(button="middle", coords=center(target[0]))
    time.sleep(1.2)
    dismiss_no(app)
    time.sleep(0.5)
    print("tabs:", [t.window_text() for t in app.wrapper.descendants(control_type="TabItem")])


main()
