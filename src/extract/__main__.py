"""CLI: python -m src.extract <image> [--llm]"""
from __future__ import annotations

import json
import sys

from .extract import extract_order


def main(argv: list[str]) -> int:
    args = [arg for arg in argv[1:] if not arg.startswith("--")]
    if not args:
        print("usage: python -m src.extract <image> [--llm]")
        return 2
    order, _ocr = extract_order(args[0], use_llm="--llm" in argv[1:])
    print(json.dumps(order.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
