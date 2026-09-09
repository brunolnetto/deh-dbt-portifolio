from datetime import date

from psycopg_pool import AsyncConnectionPool

from ...domain.products.entities import Product, ProductMetrics, ProductPerformance
from ...domain.products.repository import AbstractProductRepository

_LIST_SQL = """
    SELECT product_id, product_name, category, unit_price, is_active
    FROM analytics.dim_products
    WHERE deleted_at IS NULL
      AND (%(category)s::text    IS NULL OR category  = %(category)s::text)
      AND (%(is_active)s::boolean IS NULL OR is_active = %(is_active)s::boolean)
    ORDER BY product_name
    LIMIT %(limit)s
"""

_PERFORMANCE_SQL = """
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        COALESCE(SUM(oi.quantity), 0)                                AS items_sold,
        COALESCE(SUM(oi.amount),   0)                                AS product_revenue,
        CASE WHEN COUNT(oi.order_item_id) > 0
             THEN ROUND(AVG(oi.unit_price), 2)
             ELSE p.unit_price END                                   AS average_unit_price
    FROM analytics.dim_products p
    LEFT JOIN analytics.fct_order_items oi
           ON p.product_id = oi.product_id
          AND oi.deleted_at IS NULL
          AND (%(start_date)s::date IS NULL OR oi.created_at::date >= %(start_date)s::date)
          AND (%(end_date)s::date   IS NULL OR oi.created_at::date <= %(end_date)s::date)
    WHERE p.deleted_at IS NULL
      AND (%(category)s::text IS NULL OR p.category = %(category)s::text)
    GROUP BY p.product_id, p.product_name, p.category, p.unit_price
    ORDER BY product_revenue DESC
    LIMIT %(limit)s
"""

_METRICS_SQL = """
    SELECT
        COALESCE(SUM(quantity), 0)                                   AS items_sold,
        COALESCE(SUM(amount),   0)                                   AS product_revenue,
        CASE WHEN COUNT(*) > 0
             THEN ROUND(AVG(unit_price), 2) ELSE 0 END               AS average_unit_price
    FROM analytics.fct_order_items
    WHERE deleted_at IS NULL
      AND (%(product_id)s::bigint IS NULL OR product_id        = %(product_id)s::bigint)
      AND (%(start_date)s::date   IS NULL OR created_at::date >= %(start_date)s::date)
      AND (%(end_date)s::date     IS NULL OR created_at::date <= %(end_date)s::date)
"""


class PostgresProductRepository(AbstractProductRepository):
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_products(
        self,
        category: str | None,
        is_active: bool | None,
        limit: int,
    ) -> list[Product]:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(_LIST_SQL, {"category": category, "is_active": is_active, "limit": limit})
                rows = await cur.fetchall()
        return [
            Product(
                product_id=r[0],
                product_name=r[1],
                category=r[2],
                unit_price=r[3],
                is_active=r[4],
            )
            for r in rows
        ]

    async def get_performance(
        self,
        category: str | None,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> list[ProductPerformance]:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    _PERFORMANCE_SQL,
                    {"start_date": start_date, "end_date": end_date, "category": category, "limit": limit},
                )
                rows = await cur.fetchall()
        return [
            ProductPerformance(
                product_id=r[0],
                product_name=r[1],
                category=r[2],
                items_sold=r[3],
                product_revenue=r[4],
                average_unit_price=r[5],
            )
            for r in rows
        ]

    async def get_metrics(
        self,
        product_id: int | None,
        start_date: date | None,
        end_date: date | None,
    ) -> ProductMetrics:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    _METRICS_SQL,
                    {"product_id": product_id, "start_date": start_date, "end_date": end_date},
                )
                r = await cur.fetchone()
        return ProductMetrics(
            items_sold=r[0],
            product_revenue=r[1],
            average_unit_price=r[2],
        )
