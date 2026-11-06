import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.driver import click, get_app
from src.ui.grid import (edit_cell, grid_layout_via_llm, read_row_amounts,
                         set_grid_layout)


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break

    layout = grid_layout_via_llm(app)
    print("rows:", [(r["pos"], r["item_no"], r["y"]) for r in layout["rows"]])
    set_grid_layout(app, layout)

    print("row 2 before:", read_row_amounts(app, 2))
    edit_cell(app, 2, "qty", "3")
    print("row 2 after qty=3:", read_row_amounts(app, 2))
    print("row 1 unchanged:", read_row_amounts(app, 1))


main()
