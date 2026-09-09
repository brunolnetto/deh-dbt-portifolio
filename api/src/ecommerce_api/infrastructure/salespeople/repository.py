from datetime import date

from psycopg_pool import AsyncConnectionPool

from ...domain.salespeople.entities import Salesperson, SalespersonMetrics
from ...domain.salespeople.repository import AbstractSalespersonRepository

_LIST_SQL = """
    SELECT salesperson_id, salesperson_name, region, email
    FROM analytics.dim_salespeople
    WHERE deleted_at IS NULL
    ORDER BY salesperson_name
"""

_METRICS_SQL = """
    SELECT
        COUNT(*)                                                                   AS salesperson_orders,
        COALESCE(SUM(is_paid),    0)                                               AS salesperson_paid_orders,
        COALESCE(SUM(is_refunded), 0)                                              AS salesperson_refunded_orders,
        COALESCE(SUM(recognized_revenue), 0)                                       AS salesperson_revenue,
        COALESCE(SUM(amount), 0)                                                   AS salesperson_gmv,
        CASE WHEN COUNT(*) > 0
             THEN ROUND(SUM(amount)::numeric / COUNT(*), 2) ELSE 0 END             AS salesperson_average_order_value,
        CASE WHEN COUNT(*) > 0
             THEN ROUND(SUM(is_refunded)::numeric / COUNT(*), 4) ELSE 0 END        AS salesperson_refund_rate
    FROM analytics.fct_orders
    WHERE deleted_at IS NULL
      AND (%(salesperson_id)s::bigint IS NULL OR salesperson_id = %(salesperson_id)s::bigint)
      AND (%(start_date)s::date       IS NULL OR order_date    >= %(start_date)s::date)
      AND (%(end_date)s::date         IS NULL OR order_date    <= %(end_date)s::date)
"""


class PostgresSalespersonRepository(AbstractSalespersonRepository):
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_salespeople(self) -> list[Salesperson]:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(_LIST_SQL)
                rows = await cur.fetchall()
        return [
            Salesperson(
                salesperson_id=r[0],
                salesperson_name=r[1],
                region=r[2],
                email=r[3],
            )
            for r in rows
        ]

    async def get_metrics(
        self,
        salesperson_id: int | None,
        start_date: date | None,
        end_date: date | None,
    ) -> SalespersonMetrics:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    _METRICS_SQL,
                    {"salesperson_id": salesperson_id, "start_date": start_date, "end_date": end_date},
                )
                r = await cur.fetchone()
        return SalespersonMetrics(
            salesperson_id=salesperson_id,
            salesperson_orders=r[0],
            salesperson_paid_orders=r[1],
            salesperson_refunded_orders=r[2],
            salesperson_revenue=r[3],
            salesperson_gmv=r[4],
            salesperson_average_order_value=r[5],
            salesperson_refund_rate=r[6],
        )
