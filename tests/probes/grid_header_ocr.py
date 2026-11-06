import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.extract.ocr import run_ocr
from src.ui.driver import DUMPS, click, get_app
from src.ui.grid import grid_rect


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break

    grid = grid_rect(app)
    win = app.wrapper.rectangle()
    print("grid:", grid)
    print("window:", win)

    image = app.wrapper.capture_as_image()
    DUMPS.mkdir(exist_ok=True)
    left = grid.left - win.left
    top = grid.top - win.top
    header = image.crop((left, top, grid.right - win.left, top + 40))
    header.save(DUMPS / "grid_header.png")
    result = run_ocr(DUMPS / "grid_header.png")
    for line in result.lines:
        screen_x = grid.left + (line.left + line.right) / 2
        print(f"{line.text!r:16} box_x={line.left:6.1f}-{line.right:6.1f} "
              f"screen_x={screen_x:7.1f} offset={screen_x - grid.left:7.1f}")


main()
