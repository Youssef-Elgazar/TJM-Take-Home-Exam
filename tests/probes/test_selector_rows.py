import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.errors import ManualReviewRequired
from src.extract.schema import Address, Contact, Debtor
from src.ui.driver import click, get_app
from src.ui.selectors import select_existing_debtor


def main():
    app = get_app()
    for tab in app.wrapper.descendants(control_type="TabItem"):
        if (tab.window_text() or "").lstrip("*") == "New Order":
            click(tab)
            break

    northstar = Debtor(
        company="Northstar Office GmbH",
        contact=Contact(first_name="Marta", last_name="Klein"),
        billing=Address(zip="10117", city="Berlin"),
    )
    mam = Debtor(
        company="MAMarine",
        contact=Contact(first_name="Youssef", last_name="Elgazar"),
        billing=Address(zip="316924", city="Alexandria"),
    )
    for debtor in (northstar, mam):
        try:
            print(debtor.company, "->", select_existing_debtor(app, debtor))
        except ManualReviewRequired as exc:
            print(debtor.company, "-> not found:", exc)


main()
