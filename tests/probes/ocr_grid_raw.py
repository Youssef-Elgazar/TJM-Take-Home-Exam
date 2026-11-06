import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.extract.ocr import run_ocr
from src.ui.driver import DUMPS, click, get_app, val
from src.ui.grid import grid_rect


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break

    grid = grid_rect(app)
    print("grid:", grid)
    win = app.wrapper.rectangle()
    image = app.wrapper.capture_as_image()
    crop = image.crop((grid.left - win.left, grid.top - win.top,
                       grid.right - win.left, grid.bottom - win.top))
    DUMPS.mkdir(exist_ok=True)
    path = DUMPS / "grid_raw.png"
    crop.save(path)

    print("--- OCR lines (text | left,tright | top,bottom) ---")
    for line in run_ocr(path).lines:
        print(f"{line.text!r:40} x={line.left:6.1f}-{line.right:6.1f} "
              f"y={line.top:6.1f}-{line.bottom:6.1f}")

    print("--- totals ---")
    for name in ("Total Net", "VAT", "Total"):
        ctrl = app.spec.child_window(title=name,
                                     control_type="Edit").wrapper_object()
        print(name, repr(val(ctrl)))


main()
