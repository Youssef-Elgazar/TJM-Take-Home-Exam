"""Optional LLM extraction stage (Anthropic-compatible Messages API).

The pipeline works offline with the deterministic parser. This stage is used
only when explicitly enabled (``FAKTURAMA_USE_LLM=1`` or ``--llm``) and valid
credentials are present. If the endpoint is missing or unreachable it raises
``LlmUnavailable`` and the caller falls back to the OCR parser.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import requests

from ..config import load_dotenv
from .ocr import OcrResult
from .schema import ExtractedOrder


class LlmUnavailable(RuntimeError):
    pass


SCHEMA_HINT = """Return ONLY a JSON object with exactly these keys:
{
  "external_reference": str,
  "order_date": "YYYY-MM-DD",
  "customer_id_in_image": str,
  "currency": str,
  "debtor": {
    "company": str, "alias": str,
    "contact": {"first_name": str, "last_name": str, "email": str, "phone": str},
    "billing": {"name": str, "street": str, "zip": str, "city": str, "country": str},
    "delivery": {"name": str, "street": str, "zip": str, "city": str, "country": str}
  },
  "payment": {"method": str, "status": "PAID"|"NOT PAID", "date": "YYYY-MM-DD"},
  "items": [{"sku": str, "description": str, "qty": number, "unit": str,
             "unit_net": number, "discount_pct": number, "vat_pct": number,
             "line_net": number}],
  "totals": {"net": number, "vat": number, "gross": number}
}
Use exact strings from the image for SKU, company and payment method. Do not
invent values that are not visible. Numbers must be plain JSON numbers (no
currency symbols). If the billing and delivery addresses are identical, repeat
the same values in both."""


def _credentials() -> tuple[str, str, str]:
    load_dotenv()
    token = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get(
        "ANTHROPIC_AUTH_TOKEN")
    base = (os.environ.get("ANTHROPIC_BASE_URL")
            or "https://api.anthropic.com").rstrip("/")
    model = os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-4-5"
    if not token:
        raise LlmUnavailable("no ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN")
    return token, base, model


def _media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"


def extract_with_llm(image_path: str | Path, ocr: OcrResult,
                     timeout: float = 120.0) -> ExtractedOrder:
    token, base, model = _credentials()
    url = f"{base}{'' if base.endswith('/v1') else '/v1'}/messages"
    path = Path(image_path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")

    body = {
        "model": model,
        "max_tokens": 4096,
        "system": "You are a precise data-extraction engine. Reply with JSON only.",
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": _media_type(path),
                        "data": encoded,
                    },
                },
                {
                    "type": "text",
                    "text": f"{SCHEMA_HINT}\n\nOCR text for cross-checking:\n"
                            f"{ocr.raw_text}",
                },
            ],
        }],
    }
    try:
        response = requests.post(
            url,
            headers={
                "x-api-key": token,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise LlmUnavailable(f"LLM request failed: {exc}") from exc

    text = "".join(
        block.get("text", "")
        for block in payload.get("content", [])
        if block.get("type") == "text"
    ).strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmUnavailable(f"LLM did not return JSON: {text[:300]!r}") from exc
    return ExtractedOrder.from_dict(data)
