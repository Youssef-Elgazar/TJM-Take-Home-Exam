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
from ..ui.grid import (edit_cell, grid_layout_via_llm, read_row_amounts,
                       set_grid_layout)
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


def run(image_path: str) -> dict:
    order, ocr = extract_order(image_path)
    log("extracted:", order.external_reference, order.debtor.company,
        [item.sku for item in order.items], order.totals)

    app = get_app()
    reset_perspective(app)
    snap(app, "itc_0_start")

    # Master data first: creating products from inside an open Order makes
    # Fakturama throw a callEditor error in this build.
    log("[1] Payment method")
    code = PAYMENT_CODES.get(order.payment.method, "Mutually defined")
    payment_screen.create_payment_method(app, order.payment.method, code)

    log("[2] Products")
    for item in order.items:
        if product_screen.product_exists(app, item.sku):
            log("  exists", item.sku)
        else:
            log("  creating", item.sku)
            product_screen.create_product(app, item)

    log("[3] New Order")
    order_screen.open_new_order(app)
    order_screen.clear_all_lines(app)
    log("  date ->", order_screen.set_date(app, order.order_date))
    log("  Cust.Ref. ->",
        order_screen.set_cust_ref(app, order.external_reference))
    log("  mode ->", order_screen.set_net_mode(app))

    log("[4] Debtor")
    try:
        debtor_no = select_existing_debtor(app, order.debtor)
        log("  selected", debtor_no)
    except ManualReviewRequired:
        log("  not found; creating", order.debtor.company)
        debtor_screen.create_debtor(app, order.debtor, order.payment.method)
        order_screen.activate_order_tab(app)
        debtor_no = select_existing_debtor(app, order.debtor)
        log("  created and selected", debtor_no)
    snap(app, "itc_1_debtor")

    log("[6] Items")
    for item in order.items:
        select_existing_product(app, item.sku)
    time.sleep(1.5)

    layout = grid_layout_via_llm(app)
    set_grid_layout(app, layout)
    row_by_sku = {str(row.get("item_no", "")).strip(): row.get("pos")
                  for row in layout.get("rows", [])}
    log("  vision rows:", row_by_sku)

    for item in order.items:
        row = row_by_sku.get(item.sku)
        if row is None:
            raise ManualReviewRequired(
                f"grid row for {item.sku} not found in the vision layout")
        edit_cell(app, row, "qty", _num(item.qty))
        edit_cell(app, row, "u_price", _num(item.unit_net))
        edit_cell(app, row, "discount", _num(item.discount_pct))
        result = read_row_amounts(app, row)
        log(f"  line {row} {item.sku}: {result}")
        check(f"line {row} qty", result.get("qty"), item.qty)
        check(f"line {row} unit price", result.get("unit_price"),
              item.unit_net)
        check(f"line {row} line price", result.get("line_price"),
              item.line_net)
    snap(app, "itc_2_items")

    log("[7] Totals")
    totals = order_screen.read_totals(app)
    log("  totals:", totals)
    check("Total Net", totals.get("Total Net"), order.totals.net)
    check("VAT", totals.get("VAT"), order.totals.vat)
    check("Total", totals.get("Total"), order.totals.gross)

    log("[8] Save order")
    order_screen.save(app)
    order_number = order_screen.saved_order_number(app)
    log("  saved as", order_number)

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

    log("[10] Cleanup")
    documents.close_all_tabs(app)
    documents.open_documents(app)

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
