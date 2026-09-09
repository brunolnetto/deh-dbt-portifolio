from datetime import date

from fastapi import APIRouter, Depends, Query

from ...application.orders.queries import OrderQueries
from ...domain.orders.entities import Order, OrderMetrics
from .deps import get_order_queries

router = APIRouter()


@router.get("/", response_model=list[Order], summary="List orders")
async def list_orders(
    status: str | None = Query(None, description="pending | paid | cancelled | refunded"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    customer_id: int | None = Query(None),
    salesperson_id: int | None = Query(None),
    limit: int = Query(50, le=500),
    queries: OrderQueries = Depends(get_order_queries),
) -> list[Order]:
    return await queries.list_orders(
        status=status,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        salesperson_id=salesperson_id,
        limit=limit,
    )


@router.get("/metrics", response_model=OrderMetrics, summary="Aggregate order metrics")
async def get_order_metrics(
    status: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    queries: OrderQueries = Depends(get_order_queries),
) -> OrderMetrics:
    """
    Returns all semantic_orders.yml metrics in one call:
    order_count, purchaser_count, gross_merchandise_value, revenue,
    paid_orders, refunded_orders, refund_amount, average_order_value,
    refund_rate, refund_amount_ratio.
    """
    return await queries.get_metrics(
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
