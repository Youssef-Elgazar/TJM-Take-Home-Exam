"""Deterministic OCR parser for the labelled sales-order layout.

This is the offline fallback used when no LLM endpoint is configured. It anchors
values to field labels and slices item rows by horizontal position. It is tuned
to the synthetic "SALES ORDER INPUT" form; the LLM path in ``llm.py`` is the
general one. Every value is still re-checked by ``validate.py``.
"""
from __future__ import annotations

import re

from .ocr import OcrLine, OcrResult
from .schema import Address, Contact, Debtor, ExtractedOrder, Item, Payment, Totals

_SKU_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)+$")
_PERCENT_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_ZIP_RE = re.compile(r"[A-Za-z]*\d[A-Za-z0-9\-]*")


def _clean(text: str) -> str:
    return " ".join((text or "").split())


def _find_label(ocr: OcrResult, *names: str) -> OcrLine | None:
    for exact in (True, False):
        for name in names:
            needle = name.casefold()
            for line in ocr.lines:
                hay = _clean(line.text).casefold()
                if (hay == needle) if exact else (needle in hay):
                    return line
    return None


def _value_below(ocr: OcrResult, label: OcrLine | None,
                 max_dy: float = 36.0, x_pad: float = 20.0) -> OcrLine | None:
    if label is None:
        return None
    candidates = []
    for line in ocr.lines:
        if line is label:
            continue
        if label.bottom - 2 <= line.top <= label.bottom + max_dy:
            if (abs(line.left - label.left) <= x_pad
                    or abs(line.cx - label.cx) <= max(30.0, label.width)):
                candidates.append(line)
    if not candidates:
        return None
    candidates.sort(key=lambda item: (abs(item.top - label.bottom),
                                      abs(item.cx - label.cx)))
    return candidates[0]


def _value_text(ocr: OcrResult, label: OcrLine | None) -> str:
    line = _value_below(ocr, label)
    return _clean(line.text) if line else ""


def _block_below(ocr: OcrResult, label: OcrLine | None, count: int = 4,
                 max_dy: float = 95.0, x_pad: float = 20.0) -> list[OcrLine]:
    if label is None:
        return []
    lines = [
        line for line in ocr.lines
        if line is not label
        and label.bottom - 2 <= line.top <= label.bottom + max_dy
        and abs(line.left - label.left) <= x_pad
    ]
    lines.sort(key=lambda item: (item.top, item.left))
    return lines[:count]


def _amount(text: str | None) -> float | None:
    if not text:
        return None
    match = _NUMBER_RE.search(text.replace(",", ""))
    return float(match.group(0)) if match else None


def _percent(text: str | None) -> float | None:
    if not text:
        return None
    match = _PERCENT_RE.search(text)
    if match:
        return float(match.group(1))
    return _amount(text)


def _zip_city(text: str) -> tuple[str, str]:
    parts = _clean(text).split()
    zip_parts: list[str] = []
    city_parts: list[str] = []
    for part in parts:
        if not city_parts and _ZIP_RE.fullmatch(part):
            zip_parts.append(part)
        else:
            city_parts.append(part)
    return " ".join(zip_parts), " ".join(city_parts)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = _clean(full_name).split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def _address_block(ocr: OcrResult, label: OcrLine | None) -> Address:
    texts = [_clean(line.text) for line in _block_below(ocr, label, count=4)]
    address = Address()
    if texts:
        address.name = texts[0]
    if len(texts) > 1:
        address.street = texts[1]
    if len(texts) > 2:
        address.zip, address.city = _zip_city(texts[2])
    if len(texts) > 3:
        address.country = texts[3]
    return address


def _item_rows(ocr: OcrResult) -> list[list[OcrLine]]:
    header = _find_label(ocr, "Description")
    totals_label = _find_label(ocr, "NET TOTAL", "GROSS TOTAL")
    top = (header.bottom + 4) if header else 0.0
    bottom = (totals_label.top - 4) if totals_label else float("inf")

    rows: list[list[OcrLine]] = []
    current: list[OcrLine] = []
    for line in ocr.lines:
        if not (top <= line.top <= bottom):
            continue
        if current and abs(line.cy - current[-1].cy) > 11:
            rows.append(sorted(current, key=lambda item: item.left))
            current = []
        current.append(line)
    if current:
        rows.append(sorted(current, key=lambda item: item.left))
    return rows


def _zone(line: OcrLine, width: float) -> str:
    fraction = line.left / width
    if fraction < 0.105:
        return "pos"
    if fraction < 0.220:
        return "sku"
    if fraction < 0.440:
        return "description"
    if fraction < 0.535:
        return "qty"
    if fraction < 0.600:
        return "unit"
    if fraction < 0.685:
        return "unit_net"
    if fraction < 0.760:
        return "discount"
    if fraction < 0.835:
        return "vat"
    return "line_price"


def _row_to_item(row: list[OcrLine], width: float) -> Item | None:
    fields: dict[str, str] = {}
    for line in row:
        fields.setdefault(_zone(line, width), line.text)

    sku = _clean(fields.get("sku", ""))
    if not _SKU_RE.match(sku):
        return None
    return Item(
        sku=sku,
        description=_clean(fields.get("description", "")),
        qty=_amount(fields.get("qty")) or 0.0,
        unit=_clean(fields.get("unit", "")),
        unit_net=_amount(fields.get("unit_net")) or 0.0,
        discount_pct=_percent(fields.get("discount")) or 0.0,
        vat_pct=_percent(fields.get("vat")) or 0.0,
        line_net=_amount(fields.get("line_price")) or 0.0,
    )


def parse_ocr(ocr: OcrResult) -> ExtractedOrder:
    width = max((line.right for line in ocr.lines), default=1.0) or 1.0

    first, last = _split_name(_value_text(ocr, _find_label(ocr, "CONTACT NAME")))

    debtor = Debtor(
        company=_value_text(ocr, _find_label(ocr, "COMPANY")),
        alias=_value_text(ocr, _find_label(ocr, "CUSTOMER ALIAS", "ALIAS")),
        contact=Contact(
            first_name=first,
            last_name=last,
            email=_value_text(ocr, _find_label(ocr, "EMAIL")),
            phone=_value_text(ocr, _find_label(ocr, "PHONE")),
        ),
        billing=_address_block(ocr, _find_label(ocr, "BILLING ADDRESS")),
        delivery=_address_block(
            ocr, _find_label(ocr, "DELVERY ADDRESS", "DELIVERY ADDRESS")),
    )

    items = [item for item in
             (_row_to_item(row, width) for row in _item_rows(ocr))
             if item is not None]

    return ExtractedOrder(
        external_reference=_value_text(
            ocr, _find_label(ocr, "EXTERNAL REFERENCE")),
        order_date=_value_text(ocr, _find_label(ocr, "ORDER DATE")),
        customer_id_in_image=_value_text(ocr, _find_label(ocr, "CUSTOMER ID")),
        currency=_value_text(ocr, _find_label(ocr, "CURRENCY")),
        debtor=debtor,
        payment=Payment(
            method=_value_text(ocr, _find_label(ocr, "PAYMENT METHOD")),
            status=_value_text(ocr, _find_label(ocr, "PAID STATUS")),
            date=_value_text(ocr, _find_label(ocr, "PAYMENT DATE")),
        ),
        items=items,
        totals=Totals(
            net=_amount(_value_text(ocr, _find_label(ocr, "NET TOTAL"))) or 0.0,
            vat=_amount(_value_text(ocr, _find_label(ocr, "VAT TOTAL"))) or 0.0,
            gross=_amount(_value_text(ocr, _find_label(ocr, "GROSS TOTAL"))) or 0.0,
        ),
    )
