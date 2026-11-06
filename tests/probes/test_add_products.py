import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.screens import order as order_screen
from src.ui.driver import get_app
from src.ui.grid import (grid_rect, grid_row_centers, read_row_amounts)
from src.ui.selectors import select_existing_product


def snapshot(app, tag):
    grid = grid_rect(app)
    centers = grid_row_centers(app, grid, force=True)
    print(tag, "grid:", grid, "centers:", centers)
    for row in sorted(centers):
        print("  row", row, read_row_amounts(app, row, grid))


def main():
    app = get_app()
    order_screen.open_new_order(app)
    order_screen.clear_all_lines(app)
    snapshot(app, "after clear")

    for sku in ("CHR-ERG-01", "MAT-DESK-02"):
        print("selecting", sku)
        select_existing_product(app, sku)
        time.sleep(1.2)
        snapshot(app, "after " + sku)


main()
