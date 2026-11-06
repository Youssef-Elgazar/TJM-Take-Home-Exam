"""Extraction test: OCR + deterministic parser must reproduce the fixture."""
from __future__ import annotations

import json
from pathlib import Path

from src.extract.extract import extract_order
from src.extract.schema import ExtractedOrder, product_gross_price

ROOT = Path(__file__).resolve().parents[1]


def test_sample_extraction_matches_fixture() -> None:
    expected = ExtractedOrder.from_dict(
        json.loads((ROOT / "samples" / "expected.json").read_text(encoding="utf-8"))
    )
    order, _ocr = extract_order(ROOT / "samples" / "order_sample.png", use_llm=False)
    assert order.to_dict() == expected.to_dict()


def test_sample_key_values() -> None:
    order, _ocr = extract_order(ROOT / "samples" / "order_sample.png", use_llm=False)
    assert order.external_reference == "WEB-2026-0714-A17"
    assert order.order_date == "2026-07-14"
    assert order.debtor.company == "Northstar Office GmbH"
    assert order.debtor.contact.first_name == "Marta"
    assert order.debtor.contact.last_name == "Klein"
    assert order.debtor.billing.zip == "10117"
    assert order.debtor.delivery.zip == "10553"
    assert order.payment.method == "Bank Transfer"
    assert order.payment.is_paid
    assert [item.sku for item in order.items] == ["CHR-ERG-01", "MAT-DESK-02"]
    assert order.totals.net == 570.00
    assert order.totals.vat == 108.30
    assert order.totals.gross == 678.30


def test_product_gross_price() -> None:
    assert product_gross_price(250.00, 19) == 297.50
    assert product_gross_price(40.00, 19) == 47.60


if __name__ == "__main__":
    test_sample_extraction_matches_fixture()
    test_sample_key_values()
    test_product_gross_price()
    print("all extraction tests passed")
