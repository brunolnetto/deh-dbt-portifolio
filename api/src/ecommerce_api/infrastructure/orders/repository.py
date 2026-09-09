from datetime import date

from psycopg_pool import AsyncConnectionPool

from ...domain.orders.entities import Order, OrderMetrics
from ...domain.orders.repository import AbstractOrderRepository

_LIST_SQL = """
    SELECT
        o.order_id,
        o.customer_id,
        c.customer_name,
        o.salesperson_id,
        s.salesperson_name,
        o.order_date,
        o.status,
        o.amount,
        o.recognized_revenue,
        o.refunded_amount,
        o.deleted_at
    FROM analytics.fct_orders o
    JOIN analytics.dim_customers    c ON o.customer_id    = c.customer_id
    JOIN analytics.dim_salespeople  s ON o.salesperson_id = s.salesperson_id
    WHERE o.deleted_at IS NULL
      AND (%(status)s::text     IS NULL OR o.status         = %(status)s::text)
      AND (%(start_date)s::date IS NULL OR o.order_date     >= %(start_date)s::date)
      AND (%(end_date)s::date   IS NULL OR o.order_date     <= %(end_date)s::date)
      AND (%(customer_id)s::bigint    IS NULL OR o.customer_id    = %(customer_id)s::bigint)
      AND (%(salesperson_id)s::bigint IS NULL OR o.salesperson_id = %(salesperson_id)s::bigint)
    ORDER BY o.order_date DESC
    LIMIT %(limit)s
"""

_METRICS_SQL = """
    SELECT
        COUNT(*)                                                                  AS order_count,
        COUNT(DISTINCT customer_id)                                               AS purchaser_count,
        COALESCE(SUM(amount), 0)                                                  AS gross_merchandise_value,
        COALESCE(SUM(recognized_revenue), 0)                                      AS revenue,
        COALESCE(SUM(is_paid), 0)                                                 AS paid_orders,
        COALESCE(SUM(is_refunded), 0)                                             AS refunded_orders,
        COALESCE(SUM(refunded_amount), 0)                                         AS refund_amount,
        CASE WHEN COUNT(*) > 0
             THEN ROUND(SUM(amount)::numeric / COUNT(*), 2) ELSE 0 END            AS average_order_value,
        CASE WHEN COUNT(*) > 0
             THEN ROUND(SUM(is_refunded)::numeric / COUNT(*), 4) ELSE 0 END       AS refund_rate,
        CASE WHEN SUM(recognized_revenue) > 0
             THEN ROUND(SUM(refunded_amount)::numeric / SUM(recognized_revenue), 4)
             ELSE 0 END                                                           AS refund_amount_ratio
    FROM analytics.fct_orders
    WHERE deleted_at IS NULL
      AND (%(status)s::text     IS NULL OR status     = %(status)s::text)
      AND (%(start_date)s::date IS NULL OR order_date >= %(start_date)s::date)
      AND (%(end_date)s::date   IS NULL OR order_date <= %(end_date)s::date)
"""


class PostgresOrderRepository(AbstractOrderRepository):
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_orders(
        self,
        status: str | None,
        start_date: date | None,
        end_date: date | None,
        customer_id: int | None,
        salesperson_id: int | None,
        limit: int,
    ) -> list[Order]:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    _LIST_SQL,
                    {
                        "status": status,
                        "start_date": start_date,
                        "end_date": end_date,
                        "customer_id": customer_id,
                        "salesperson_id": salesperson_id,
                        "limit": limit,
                    },
                )
                rows = await cur.fetchall()
        return [
            Order(
                order_id=r[0],
                customer_id=r[1],
                customer_name=r[2],
                salesperson_id=r[3],
                salesperson_name=r[4],
                order_date=r[5],
                status=r[6],
                amount=r[7],
                recognized_revenue=r[8],
                refunded_amount=r[9],
                deleted_at=r[10],
            )
            for r in rows
        ]

    async def get_metrics(
        self,
        status: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> OrderMetrics:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    _METRICS_SQL,
                    {"status": status, "start_date": start_date, "end_date": end_date},
                )
                r = await cur.fetchone()
        return OrderMetrics(
            order_count=r[0],
            purchaser_count=r[1],
            gross_merchandise_value=r[2],
            revenue=r[3],
            paid_orders=r[4],
            refunded_orders=r[5],
            refund_amount=r[6],
            average_order_value=r[7],
            refund_rate=r[8],
            refund_amount_ratio=r[9],
        )
