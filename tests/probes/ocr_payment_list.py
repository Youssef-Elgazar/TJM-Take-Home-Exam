import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.extract.ocr import run_ocr
from src.ui.driver import DUMPS, click, get_app


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").strip() == "terms of payment":
            click(tab)
            break
    win = app.wrapper.rectangle()
    image = app.wrapper.capture_as_image()
    top = max(0, 700 - win.top)
    crop = image.crop((0, top, image.width, image.height))
    DUMPS.mkdir(exist_ok=True)
    path = DUMPS / "terms_list.png"
    crop.save(path)
    outlines = [f"{line.text!r} ({line.left:.0f},{line.top:.0f})"
                for line in run_ocr(path).lines]
    (DUMPS / "terms_list_ocr.txt").write_text("\n".join(outlines),
                                              encoding="utf-8")
    print("wrote", len(outlines), "lines")


main()
