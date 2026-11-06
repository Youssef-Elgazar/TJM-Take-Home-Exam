"""Typed model for the extracted order plus JSON (de)serialisation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


def product_gross_price(unit_net: float, vat_pct: float) -> float:
    """Product master price: unit net x (1 + VAT%), rounded to 2 dp."""
    return round(unit_net * (1.0 + vat_pct / 100.0), 2)


def line_net_price(qty: float, unit_net: float, discount_pct: float) -> float:
    return round(qty * unit_net * (1.0 - discount_pct / 100.0), 2)


@dataclass
class Contact:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""


@dataclass
class Address:
    name: str = ""
    street: str = ""
    zip: str = ""
    city: str = ""
    country: str = ""


@dataclass
class Debtor:
    company: str = ""
    alias: str = ""
    contact: Contact = field(default_factory=Contact)
    billing: Address = field(default_factory=Address)
    delivery: Address = field(default_factory=Address)


@dataclass
class Payment:
    method: str = ""
    status: str = ""
    date: str = ""

    @property
    def is_paid(self) -> bool:
        return self.status.strip().upper() == "PAID"


@dataclass
class Item:
    sku: str = ""
    description: str = ""
    qty: float = 0.0
    unit: str = ""
    unit_net: float = 0.0
    discount_pct: float = 0.0
    vat_pct: float = 0.0
    line_net: float = 0.0


@dataclass
class Totals:
    net: float = 0.0
    vat: float = 0.0
    gross: float = 0.0


@dataclass
class ExtractedOrder:
    external_reference: str = ""
    order_date: str = ""
    customer_id_in_image: str = ""
    currency: str = ""
    debtor: Debtor = field(default_factory=Debtor)
    payment: Payment = field(default_factory=Payment)
    items: list[Item] = field(default_factory=list)
    totals: Totals = field(default_factory=Totals)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractedOrder":
        """Accept both the flat shape and the handover fixture shape."""
        order = data.get("order", data)
        debtor = data.get("debtor", {})
        contact = debtor.get("contact", {})
        billing = debtor.get("billing", {})
        delivery = debtor.get("delivery", {})
        payment = data.get("payment", {})
        totals = data.get("totals", {})

        def amount(value) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        def text(value) -> str:
            return "" if value is None else str(value)

        return cls(
            external_reference=text(order.get("external_reference")),
            order_date=text(order.get("order_date")),
            customer_id_in_image=text(order.get("customer_id_in_image")),
            currency=text(order.get("currency")),
            debtor=Debtor(
                company=text(debtor.get("company")),
                alias=text(debtor.get("alias")),
                contact=Contact(
                    first_name=text(contact.get("first_name")),
                    last_name=text(contact.get("last_name")),
                    email=text(contact.get("email")),
                    phone=text(contact.get("phone")),
                ),
                billing=Address(
                    name=text(billing.get("name")),
                    street=text(billing.get("street")),
                    zip=text(billing.get("zip")),
                    city=text(billing.get("city")),
                    country=text(billing.get("country")),
                ),
                delivery=Address(
                    name=text(delivery.get("name")),
                    street=text(delivery.get("street")),
                    zip=text(delivery.get("zip")),
                    city=text(delivery.get("city")),
                    country=text(delivery.get("country")),
                ),
            ),
            payment=Payment(
                method=text(payment.get("method")),
                status=text(payment.get("status")),
                date=text(payment.get("date")),
            ),
            items=[
                Item(
                    sku=text(item.get("sku")),
                    description=text(item.get("description")),
                    qty=amount(item.get("qty")),
                    unit=text(item.get("unit")),
                    unit_net=amount(item.get("unit_net")),
                    discount_pct=amount(item.get("discount_pct")),
                    vat_pct=amount(item.get("vat_pct")),
                    line_net=amount(item.get("line_net")),
                )
                for item in data.get("items", [])
            ],
            totals=Totals(
                net=amount(totals.get("net")),
                vat=amount(totals.get("vat")),
                gross=amount(totals.get("gross")),
            ),
        )
