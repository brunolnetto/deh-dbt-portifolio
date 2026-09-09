from decimal import Decimal

from pydantic import BaseModel


class Salesperson(BaseModel):
    salesperson_id: int
    salesperson_name: str
    region: str
    email: str


class SalespersonMetrics(BaseModel):
    """Per-salesperson metrics. Mirrors semantic_salespeople.yml."""

    salesperson_id: int | None = None
    salesperson_orders: int
    salesperson_paid_orders: int
    salesperson_refunded_orders: int
    salesperson_revenue: Decimal
    salesperson_gmv: Decimal
    salesperson_average_order_value: Decimal
    salesperson_refund_rate: Decimal
