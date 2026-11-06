import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.driver import click, get_app
from src.ui.grid import read_row_amounts, grid_row_centers, grid_rect


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break
    grid = grid_rect(app)
    print("grid:", grid)
    print("centers:", grid_row_centers(app, grid))
    print("row 1:", read_row_amounts(app, 1))
    print("row 2:", read_row_amounts(app, 2))
    print("row 3:", read_row_amounts(app, 3))


main()
