"""Full image -> master data -> Order -> Invoice flow."""
from __future__ import annotations

import sys
import time

from ..errors import ManualReviewRequired
from ..extract.extract import extract_order
from ..screens import debtor as debtor_screen
from ..screens import documents
from ..screens import invoice as invoice_screen
from ..screens import order as order_screen
from ..screens import payment as payment_screen
from ..screens import product as product_screen
from ..ui.driver import get_app, reset_perspective, snap
from ..ui.grid import edit_cell, read_row_amounts, wait_for_row
from ..ui.selectors import select_existing_debtor, select_existing_product

PAYMENT_CODES = {
    "Bank Transfer": "Credit transfer",
    "Credit Card": "Credit card",
    "SEPA Direct Debit": "SEPA direct debit",
}
TOLERANCE = 0.01


def log(*parts) -> None:
    print(*parts, flush=True)


def check(label: str, actual, expected: float) -> None:
    if actual is None or abs(actual - expected) > TOLERANCE:
        raise ManualReviewRequired(
            f"{label}: expected {expected:.2f}, got {actual}")
    log(f"  ok {label} = {actual:.2f}")


def _num(value) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:.2f}"


# Per-stage wall-clock timings, printed at the end of the run.
_STAGE_TIMES: list[tuple[str, float]] = []
_STAGE_LAST = time.perf_counter()


def stage(name: str) -> None:
    """Record the elapsed time since the previous ``stage`` call."""
    global _STAGE_LAST
    now = time.perf_counter()
    _STAGE_TIMES.append((name, now - _STAGE_LAST))
    _STAGE_LAST = now


def report_timings() -> None:
    log("---- stage timings ----")
    for name, seconds in _STAGE_TIMES:
        log(f"  {name:28s} {seconds:6.2f}s")
    log(f"  {'TOTAL':28s} {sum(s for _, s in _STAGE_TIMES):6.2f}s")


def run(image_path: str) -> dict:
    global _STAGE_LAST
    _STAGE_TIMES.clear()
    _STAGE_LAST = time.perf_counter()

    # Bring the app up and reset its perspective first, so we are not sitting
    # idle on the home page while the image extraction runs.
    app = get_app()
    reset_perspective(app)
    snap(app, "itc_0_start")
    stage("startup")

    order, ocr = extract_order(image_path)
    log("extracted:", order.external_reference, order.debtor.company,
        [item.sku for item in order.items], order.totals)
    stage("extract")

    # Master data first: creating products from inside an open Order makes
    # Fakturama throw a callEditor error in this build.
    log("[1] Payment method")
    code = PAYMENT_CODES.get(order.payment.method, "Mutually defined")
    payment_screen.create_payment_method(app, order.payment.method, code)
    stage("payment method")

    log("[2] Products")
    for item in order.items:
        if product_screen.product_exists(app, item.sku):
            log("  exists", item.sku)
        else:
            log("  creating", item.sku)
            product_screen.create_product(app, item)
    stage("products")

    log("[3] Debtor")
    if debtor_screen.debtor_exists(app, order.debtor):
        log("  exists", order.debtor.company)
    else:
        log("  creating", order.debtor.company)
        debtor_screen.create_debtor(app, order.debtor, order.payment.method)
    stage("debtor")

    log("[4] New Order")
    order_screen.open_new_order(app)
    order_screen.clear_all_lines(app)
    log("  date ->", order_screen.set_date(app, order.order_date))
    log("  Cust.Ref. ->",
        order_screen.set_cust_ref(app, order.external_reference))
    log("  mode ->", order_screen.set_net_mode(app))
    stage("new order")

    log("[5] Debtor select")
    debtor_no = select_existing_debtor(app, order.debtor)
    log("  selected", debtor_no)
    snap(app, "itc_1_debtor")
    stage("debtor select")

    log("[6] Items")
    for index, item in enumerate(order.items, start=1):
        select_existing_product(app, item.sku)
        wait_for_row(app, index, item.sku)
        edit_cell(app, index, "qty", _num(item.qty))
        edit_cell(app, index, "discount", _num(item.discount_pct))
        result = read_row_amounts(app, index)
        log(f"  line {index} {item.sku}: {result}")
        check(f"line {index} qty", result.get("qty"), item.qty)
        check(f"line {index} unit price", result.get("unit_price"),
              item.unit_net)
        check(f"line {index} line price", result.get("line_price"),
              item.line_net)
    snap(app, "itc_2_items")
    stage("items")

    log("[7] Totals")
    totals = order_screen.read_totals(app)
    log("  totals:", totals)
    check("Total Net", totals.get("Total Net"), order.totals.net)
    check("VAT", totals.get("VAT"), order.totals.vat)
    check("Total", totals.get("Total"), order.totals.gross)
    stage("totals check")

    log("[8] Save order")
    order_screen.save(app)
    order_number = order_screen.saved_order_number(app)
    log("  saved as", order_number)
    stage("save order")

    log("[9] Invoice")
    invoice_screen.create_followup_invoice(app)
    log("  payment ->",
        invoice_screen.set_payment_method(app, order.payment.method))
    if order.payment.is_paid:
        log("  paid at ->", invoice_screen.set_paid(app, order.payment.date))
        log("  value ->",
            invoice_screen.set_value(app, f"{order.totals.gross:.2f}"))
    snap(app, "itc_3_invoice")
    invoice_screen.save(app)
    invoice_number = invoice_screen.invoice_number(app)
    log("  saved invoice", invoice_number)

    totals = invoice_screen.read_totals(app)
    log("  invoice totals:", totals)
    check("Invoice Total Net", totals.get("Total Net"), order.totals.net)
    check("Invoice VAT", totals.get("VAT"), order.totals.vat)
    check("Invoice Total", totals.get("Total"), order.totals.gross)
    stage("invoice")

    log("[10] Cleanup")
    documents.close_all_tabs(app)
    documents.open_documents(app)
    stage("cleanup")

    report_timings()
    log("IMAGE->CASH OK")
    return {"order": order_number, "invoice": invoice_number,
            "totals": totals}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m src.flows.image_to_cash <image>")
        return 2
    run(argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
