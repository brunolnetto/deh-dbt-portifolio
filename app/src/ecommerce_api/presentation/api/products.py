from datetime import date

from fastapi import APIRouter, Depends, Query

from ...application.products.queries import ProductQueries
from ...domain.products.entities import Product, ProductMetrics, ProductPerformance
from .deps import get_product_queries

router = APIRouter()


@router.get("/", response_model=list[Product], summary="List products")
async def list_products(
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
    limit: int = Query(100, le=500),
    queries: ProductQueries = Depends(get_product_queries),
) -> list[Product]:
    return await queries.list_products(
        category=category,
        is_active=is_active,
        limit=limit,
    )


@router.get(
    "/performance",
    response_model=list[ProductPerformance],
    summary="Per-product performance metrics",
)
async def get_product_performance(
    category: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(50, le=200),
    queries: ProductQueries = Depends(get_product_queries),
) -> list[ProductPerformance]:
    """
    Returns items_sold, product_revenue, and average_unit_price
    per product (semantic_products.yml measures).
    """
    return await queries.get_performance(
        category=category,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/metrics", response_model=ProductMetrics, summary="Aggregate product metrics")
async def get_product_metrics(
    product_id: int | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    queries: ProductQueries = Depends(get_product_queries),
) -> ProductMetrics:
    """
    Returns items_sold, product_revenue, average_unit_price
    aggregated across all (or one) product.
    """
    return await queries.get_metrics(
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
    )
