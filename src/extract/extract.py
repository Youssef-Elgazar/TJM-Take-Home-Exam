"""Image -> validated ExtractedOrder orchestration."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from ..config import load_dotenv
from .llm import LlmUnavailable, extract_with_llm
from .ocr import OcrResult, run_ocr
from .parser import parse_ocr
from .schema import ExtractedOrder
from .validate import validate


def extract_order(image_path: str | Path,
                  use_llm: bool | None = None) -> tuple[ExtractedOrder, OcrResult]:
    """Extract, parse and validate an order image.

    Returns (order, ocr_result). Raises ManualReviewRequired when validation
    fails. The LLM stage is optional and falls back to the deterministic parser.
    """
    load_dotenv()
    if use_llm is None:
        use_llm = os.environ.get("FAKTURAMA_USE_LLM", "").strip().lower() in {
            "1", "true", "yes", "on"
        }

    ocr = run_ocr(image_path)
    order: ExtractedOrder | None = None
    if use_llm:
        try:
            order = extract_with_llm(image_path, ocr)
        except LlmUnavailable as exc:
            print(f"[extract] LLM unavailable, using the OCR parser: {exc}",
                  file=sys.stderr)
            order = None
    if order is None:
        order = parse_ocr(ocr)

    validate(order, ocr.raw_text)
    return order, ocr
