import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.extract.llm import read_grid_with_llm
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
    image = app.wrapper.capture_as_image()
    crop = image.crop((grid.left - win.left, grid.top - win.top,
                       grid.right - win.left, grid.bottom - win.top))
    DUMPS.mkdir(exist_ok=True)
    path = DUMPS / "grid_llm.png"
    crop.save(path)
    print("grid:", grid, "crop:", crop.size)
    print(json.dumps(read_grid_with_llm(path), indent=2))


main()
