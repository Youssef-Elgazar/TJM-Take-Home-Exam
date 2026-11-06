"""Minimal .env loader (no extra dependency).

Keys present in ``.env`` take precedence over the process environment, so the
file is the single source of truth for local runs. Blank values are ignored.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path | None = None) -> None:
    env_path = (Path(path) if path is not None
                else Path(__file__).resolve().parents[1] / ".env")
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            os.environ[key] = value
