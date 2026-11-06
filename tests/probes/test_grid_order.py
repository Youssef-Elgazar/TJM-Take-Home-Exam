import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.extract.ocr import run_ocr
from src.screens import order as order_screen
from src.ui.driver import DUMPS, get_app
from src.ui.grid import grid_rect, grid_row_centers, read_row_amounts
from src.ui.selectors import select_existing_product


def main():
    app = get_app()
    order_screen.open_new_order(app)
    order_screen.clear_all_lines(app)
    for sku in ("CHR-ERG-01", "MAT-DESK-02"):
        select_existing_product(app, sku)

    print("row 1:", read_row_amounts(app, 1))
    print("row 2:", read_row_amounts(app, 2))

    grid = grid_rect(app)
    print("grid:", grid)
    print("centers:", grid_row_centers(app, grid, force=True))

    win = app.wrapper.rectangle()
    image = app.wrapper.capture_as_image()
    crop = image.crop((grid.left - win.left, grid.top - win.top,
                       grid.right - win.left, grid.bottom - win.top))
    DUMPS.mkdir(exist_ok=True)
    path = DUMPS / "grid_raw.png"
    crop.save(path)
    print("--- OCR lines ---")
    for line in run_ocr(path).lines:
        print(f"{line.text!r:40} x={line.left:6.1f}-{line.right:6.1f} "
              f"y={line.top:6.1f}-{line.bottom:6.1f}")


main()
