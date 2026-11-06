"""RapidOCR wrapper: returns text with confidence and boxes in reading order."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _add_nvidia_dll_dirs() -> None:
    """Put pip-installed NVIDIA CUDA/cuDNN ``bin`` dirs on the DLL search path.

    onnxruntime-gpu needs ``cudnn64_9.dll`` (and friends) at runtime; the
    ``nvidia-*-cu12`` wheels drop them under ``site-packages/nvidia/<pkg>/bin``,
    which is not on ``PATH`` by default.
    """
    try:
        nvidia = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
        if not nvidia.is_dir():
            return
        existing = set(os.environ.get("PATH", "").split(os.pathsep))
        bins = [str(p / "bin") for p in nvidia.iterdir()
                if (p / "bin").is_dir()]
        added = [b for b in bins if b not in existing]
        if added:
            os.environ["PATH"] = os.pathsep.join(
                added + [os.environ.get("PATH", "")])
    except Exception:
        pass


_add_nvidia_dll_dirs()


@dataclass
class OcrLine:
    text: str
    score: float
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def cy(self) -> float:
        return (self.top + self.bottom) / 2.0

    @property
    def cx(self) -> float:
        return (self.left + self.right) / 2.0


@dataclass
class OcrResult:
    lines: list[OcrLine] = field(default_factory=list)

    @property
    def raw_text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    def find(self, needle: str, casefold: bool = True) -> list[OcrLine]:
        needle = needle.casefold() if casefold else needle
        hits = []
        for line in self.lines:
            hay = line.text.casefold() if casefold else line.text
            if needle in hay:
                hits.append(line)
        return hits


def _box_to_rect(box) -> tuple[float, float, float, float]:
    xs = [float(point[0]) for point in box]
    ys = [float(point[1]) for point in box]
    return min(xs), min(ys), max(xs), max(ys)


def _reading_order(lines: list[OcrLine], row_tolerance: float = 12.0) -> list[OcrLine]:
    """Group into approximate text rows, then order left-to-right within a row."""
    if not lines:
        return []
    rows: list[list[OcrLine]] = []
    for line in sorted(lines, key=lambda item: (item.top, item.left)):
        for row in rows:
            reference = row[0]
            if abs(reference.cy - line.cy) <= row_tolerance:
                row.append(line)
                break
        else:
            rows.append([line])
    ordered: list[OcrLine] = []
    for row in sorted(rows, key=lambda group: min(item.top for item in group)):
        ordered.extend(sorted(row, key=lambda item: item.left))
    return ordered


_engine = None


def _cuda_available() -> bool:
    """True when onnxruntime ships a working CUDAExecutionProvider."""
    try:
        import onnxruntime as ort
        return ("CUDAExecutionProvider" in ort.get_available_providers()
                and ort.get_device() == "GPU")
    except Exception:
        return False


def get_engine():
    """Lazily create the RapidOCR engine (model load is expensive).

    Uses the CUDA (GPU) execution provider when onnxruntime-gpu is installed
    and actually runs (a missing cuDNN is detected and falls back to CPU).
    Engine creation is cached so the models load only once per process.
    """
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR

        if _cuda_available():
            import numpy as np
            probe = np.full((32, 32, 3), 255, dtype=np.uint8)
            try:
                engine = RapidOCR(params={
                    "EngineConfig.onnxruntime.use_cuda": True,
                    # The grid crops vary in size on every call; EXHAUSTIVE
                    # cuDNN algorithm search re-optimises per shape and stalls.
                    "EngineConfig.onnxruntime.cuda_ep_cfg."
                    "cudnn_conv_algo_search": "HEURISTIC",
                })
                engine(probe)  # force the models to load; raises without cuDNN
                _engine = engine
                return _engine
            except Exception as exc:
                print(f"[ocr] CUDA engine unusable ({exc}); using CPU",
                      file=sys.stderr)
        _engine = RapidOCR()
    return _engine


def run_ocr(image_path: str | Path) -> OcrResult:
    result = get_engine()(str(image_path))
    lines: list[OcrLine] = []
    texts = result.txts or ()
    scores = result.scores or ()
    boxes = result.boxes if result.boxes is not None else ()
    for text, score, box in zip(texts, scores, boxes):
        if not (text or "").strip():
            continue
        left, top, right, bottom = _box_to_rect(box)
        lines.append(
            OcrLine(
                text=str(text).strip(),
                score=float(score),
                left=left,
                top=top,
                right=right,
                bottom=bottom,
            )
        )
    return OcrResult(lines=_reading_order(lines))
