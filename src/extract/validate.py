"""Deterministic validation and totals recomputation for the extracted order."""
from __future__ import annotations

import re

from ..errors import ManualReviewRequired
from .schema import ExtractedOrder, line_net_price

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SKU_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)+$")
_TOLERANCE = 0.01


def _normalise(text: str) -> str:
    return " ".join((text or "").split()).casefold()


def _in_raw(value: str, raw: str) -> bool:
    return _normalise(value) in _normalise(raw)


def validate(order: ExtractedOrder, raw_text: str | None = None) -> None:
    reasons: list[str] = []

    if not order.external_reference:
        reasons.append("external reference is missing")
    if not order.order_date:
        reasons.append("order date is missing")
    elif not _DATE_RE.match(order.order_date):
        reasons.append(f"order date is not ISO yyyy-mm-dd: {order.order_date!r}")
    if not order.debtor.company:
        reasons.append("debtor company is missing")
    if not order.items:
        reasons.append("no item lines were extracted")

    email = order.debtor.contact.email
    if email and not _EMAIL_RE.match(email):
        reasons.append(f"contact e-mail looks invalid: {email!r}")

    payment_date = order.payment.date
    if payment_date and not _DATE_RE.match(payment_date):
        reasons.append(f"payment date is not ISO yyyy-mm-dd: {payment_date!r}")

    # Recompute each line and the document totals from the primitives.
    for index, item in enumerate(order.items, start=1):
        if not _SKU_RE.match(item.sku):
            reasons.append(f"line {index}: SKU looks invalid: {item.sku!r}")
        if item.qty <= 0:
            reasons.append(f"line {index}: quantity must be positive")
        expected_line = line_net_price(item.qty, item.unit_net, item.discount_pct)
        if abs(expected_line - item.line_net) > _TOLERANCE:
            reasons.append(
                f"line {index} ({item.sku}): price {item.line_net:.2f} "
                f"!= qty x net x (1-disc) = {expected_line:.2f}"
            )

    net = round(sum(item.line_net for item in order.items), 2)
    vat = round(sum(item.line_net * item.vat_pct / 100.0
                    for item in order.items), 2)
    gross = round(net + vat, 2)

    for label, actual, expected in (
        ("net", order.totals.net, net),
        ("VAT", order.totals.vat, vat),
        ("gross", order.totals.gross, gross),
    ):
        if abs(actual - expected) > _TOLERANCE:
            reasons.append(
                f"{label} total {actual:.2f} != recomputed {expected:.2f}")

    # Guard against hallucinated values: key strings must appear in the OCR text.
    if raw_text is not None:
        for value, label in (
            (order.external_reference, "external reference"),
            (order.debtor.company, "company"),
        ):
            if value and not _in_raw(value, raw_text):
                reasons.append(
                    f"{label} {value!r} does not appear in the OCR text")
        for item in order.items:
            if item.sku and not _in_raw(item.sku, raw_text):
                reasons.append(
                    f"SKU {item.sku!r} does not appear in the OCR text")

    if reasons:
        raise ManualReviewRequired(reasons)
