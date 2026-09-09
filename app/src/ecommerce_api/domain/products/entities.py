from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class Product(BaseModel):
    product_id: int
    product_name: str
    category: str
    unit_price: Decimal
    is_active: bool


class ProductPerformance(BaseModel):
    """Per-product metrics. Mirrors semantic_products.yml measures."""

    product_id: int
    product_name: str
    category: str
    items_sold: int
    product_revenue: Decimal
    average_unit_price: Decimal


class ProductMetrics(BaseModel):
    """Aggregate metrics across all products. Mirrors semantic_products.yml."""

    items_sold: int
    product_revenue: Decimal
    average_unit_price: Decimal
