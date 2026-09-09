from datetime import date

from fastapi import APIRouter, Depends, Query

from ...application.salespeople.queries import SalespersonQueries
from ...domain.salespeople.entities import Salesperson, SalespersonMetrics
from .deps import get_salesperson_queries

router = APIRouter()


@router.get("/", response_model=list[Salesperson], summary="List salespeople")
async def list_salespeople(
    queries: SalespersonQueries = Depends(get_salesperson_queries),
) -> list[Salesperson]:
    return await queries.list_salespeople()


@router.get(
    "/metrics",
    response_model=SalespersonMetrics,
    summary="Salesperson metrics (aggregate or per-person)",
)
async def get_salesperson_metrics(
    salesperson_id: int | None = Query(None, description="Omit for all salespeople combined"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    queries: SalespersonQueries = Depends(get_salesperson_queries),
) -> SalespersonMetrics:
    """
    Returns all semantic_salespeople.yml metrics:
    salesperson_orders, salesperson_paid_orders, salesperson_refunded_orders,
    salesperson_revenue, salesperson_gmv, salesperson_average_order_value,
    salesperson_refund_rate.
    """
    return await queries.get_metrics(
        salesperson_id=salesperson_id,
        start_date=start_date,
        end_date=end_date,
    )
