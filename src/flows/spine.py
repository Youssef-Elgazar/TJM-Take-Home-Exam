"""Spine flow: Order -> existing debtor -> existing product -> Invoice.

This is the first-version path. It deliberately does **not** create master data:
if the debtor or product is missing it stops with ManualReviewRequired. The
creation branches are added once the spine is proven.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ..errors import ManualReviewRequired
from ..extract.schema import ExtractedOrder
from ..screens import invoice as invoice_screen
from ..screens import order as order_screen
from ..ui.driver import get_app, snap
from ..ui.selectors import select_existing_debtor

TOLERANCE = 0.01


def log(*parts) -> None:
    print(*parts, flush=True)


def check(label: str, actual, expected: float) -> None:
    if actual is None or abs(actual - expected) > TOLERANCE:
        raise ManualReviewRequired(
            f"{label}: expected {expected:.2f}, got {actual}")
    log(f"  ok {label} = {actual:.2f}")


def run_spine(fixture_path: str | Path) -> dict:
    expected = ExtractedOrder.from_dict(
        json.loads(Path(fixture_path).read_text(encoding="utf-8")))

    app = get_app()
    snap(app, "spine_0_start")

    log("[1] New Order")
    order_screen.open_new_order(app)
    order_screen.clear_all_lines(app)
    log("  date ->", order_screen.set_date(app, expected.order_date))
    log("  Cust.Ref. ->",
        order_screen.set_cust_ref(app, expected.external_reference))
    log("  mode ->", order_screen.set_net_mode(app))

    log("[2] Debtor")
    debtor_no = select_existing_debtor(app, expected.debtor)
    log("  selected debtor", debtor_no)
    snap(app, "spine_1_debtor")

    log("[3] Items")
    for index, item in enumerate(expected.items, start=1):
        result = order_screen.add_order_line(app, item, index)
        log(f"  line {index} {item.sku}: {result}")
        check(f"line {index} qty", result.get("qty"), item.qty)
        check(f"line {index} unit price", result.get("unit_price"),
              item.unit_net)
        check(f"line {index} line price", result.get("line_price"),
              item.line_net)
    snap(app, "spine_2_items")

    log("[4] Totals")
    totals = order_screen.read_totals(app)
    log("  totals:", totals)
    check("Total Net", totals.get("Total Net"), expected.totals.net)
    check("VAT", totals.get("VAT"), expected.totals.vat)
    check("Total", totals.get("Total"), expected.totals.gross)

    log("[5] Save order")
    order_screen.save(app)
    order_number = order_screen.saved_order_number(app)
    log("  saved as", order_number)
    snap(app, "spine_3_saved")

    log("[6] Create linked invoice")
    invoice_screen.create_followup_invoice(app)
    log("  payment ->",
        invoice_screen.set_payment_method(app, expected.payment.method))
    if expected.payment.is_paid:
        log("  paid at ->", invoice_screen.set_paid(app,
                                                   expected.payment.date))
        log("  value ->",
            invoice_screen.set_value(app, f"{expected.totals.gross:.2f}"))
    snap(app, "spine_4_invoice")
    invoice_screen.save(app)
    invoice_number = invoice_screen.invoice_number(app)
    log("  saved invoice", invoice_number)

    log("[7] Verify invoice totals")
    totals = invoice_screen.read_totals(app)
    log("  totals:", totals)
    check("Invoice Total Net", totals.get("Total Net"), expected.totals.net)
    check("Invoice VAT", totals.get("VAT"), expected.totals.vat)
    check("Invoice Total", totals.get("Total"), expected.totals.gross)
    snap(app, "spine_5_verified")

    log("SPINE OK")
    return {"order": order_number, "invoice": invoice_number,
            "totals": totals}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m src.flows.spine <fixture.json>")
        return 2
    run_spine(argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
