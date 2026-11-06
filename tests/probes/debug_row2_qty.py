import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.driver import click, get_app
from src.ui.grid import (edit_cell, grid_rect, grid_row_centers,
                         read_row_amounts)


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break
    grid = grid_rect(app)
    print("grid:", grid)
    print("centers:", grid_row_centers(app, grid, force=True))
    print("row 1:", read_row_amounts(app, 1))
    print("row 2:", read_row_amounts(app, 2))
    edit_cell(app, 2, "qty", "3")
    print("row 2 after qty=3:", read_row_amounts(app, 2))
    print("row 1 after qty=3:", read_row_amounts(app, 1))


main()
