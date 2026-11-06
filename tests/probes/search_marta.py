import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.driver import click, get_app
from src.ui.grid import address_icons
from src.ui.selectors import _walk_rows


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break
    icons = address_icons(app)
    click(icons[0])
    dialog_spec = app.spec.child_window(title="Select the address",
                                        control_type="Window")
    dialog_spec.wait("exists", timeout=8)
    dialog = dialog_spec.wrapper_object()
    search = dialog_spec.child_window(control_type="Edit")
    for term in ("Marta", "Northstar", "GmbH"):
        search.set_edit_text(term)
        time.sleep(1.2)
        rows = _walk_rows(app, dialog, search.rectangle())
        print(term, "->", rows)
    if dialog_spec.exists():
        dialog_spec.child_window(title="Cancel",
                                 control_type="Button").click_input()


main()
