"""Finish the invoice left open by the spine run and verify it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.screens import invoice as invoice_screen
from src.ui.driver import click, get_app


def main():
    app = get_app()
    invoice_tab = None
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Invoice":
            invoice_tab = tab
            break
    if invoice_tab is None:
        print("no invoice tab")
        return
    click(invoice_tab)
    print("paid at ->", invoice_screen.set_paid(app, "2026-07-18"))
    print("value ->", invoice_screen.set_value(app, "214.20"))
    invoice_screen.save(app)
    print("invoice ->", invoice_screen.invoice_number(app))
    print("totals ->", invoice_screen.read_totals(app))
    print("paid state ->", invoice_screen.paid_checkbox(app).get_toggle_state())


main()
