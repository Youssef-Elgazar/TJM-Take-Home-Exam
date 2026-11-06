import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.driver import click, get_app
from src.ui.grid import (grid_rect, grid_row_centers, read_row_amounts,
                         wait_for_row)


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break

    for i in range(4):
        grid = grid_rect(app)
        centers = grid_row_centers(app, grid, force=True)
        row2 = read_row_amounts(app, 2, grid) if 2 in centers else None
        print(i, "grid:", grid, "centers:", centers, "row2:", row2)
        time.sleep(0.5)

    try:
        print("wait_for_row:", wait_for_row(app, 2, "MAT-DESK-02", timeout=6))
    except Exception as exc:
        print("wait_for_row FAILED:", exc)


main()
