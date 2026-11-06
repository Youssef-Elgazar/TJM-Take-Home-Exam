import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.driver import click, get_app
from src.ui.grid import edit_cell, read_row_amounts


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break

    print("before row 1:", read_row_amounts(app, 1))
    print("before row 2:", read_row_amounts(app, 2))

    edit_cell(app, 2, "qty", "3")
    print("after row2 qty=3, row 1:", read_row_amounts(app, 1))
    print("after row2 qty=3, row 2:", read_row_amounts(app, 2))

    edit_cell(app, 1, "qty", "2")
    print("after row1 qty=2, row 1:", read_row_amounts(app, 1))
    print("after row1 qty=2, row 2:", read_row_amounts(app, 2))


main()
