from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

OrderStatus = Literal["pending", "paid", "cancelled", "refunded"]


class Order(BaseModel):
    order_id: int
    customer_id: int
    customer_name: str
    salesperson_id: int
    salesperson_name: str
    order_date: date
    status: OrderStatus
    amount: Decimal
    recognized_revenue: Decimal
    refunded_amount: Decimal
    deleted_at: datetime | None = None


class OrderMetrics(BaseModel):
    """Mirrors the measures and metrics in semantic_orders.yml."""

    order_count: int
    purchaser_count: int
    gross_merchandise_value: Decimal
    revenue: Decimal
    paid_orders: int
    refunded_orders: int
    refund_amount: Decimal
    average_order_value: Decimal
    refund_rate: Decimal
    refund_amount_ratio: Decimal
