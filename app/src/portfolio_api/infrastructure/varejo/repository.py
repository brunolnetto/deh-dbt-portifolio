"""Varejo domain queries against analytics_varejo schema."""

from datetime import date
from typing import Any

from psycopg_pool import AsyncConnectionPool


class VarejoRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_clientes(
        self,
        state: str | None = None,
        segment: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if state:
            conditions.append(f"state = ${len(params) + 1}")
            params.append(state.upper())
        if segment:
            conditions.append(f"segment = ${len(params) + 1}")
            params.append(segment)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT customer_id, customer_name, state, state_name,
                       region, segment, registered_at
                FROM analytics_varejo.dim_clientes
                {where}
                ORDER BY customer_id
                LIMIT ${len(params)}
                """,
                params,
            )
            return [dict(row) async for row in rows]

    async def list_produtos(
        self,
        category: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if category:
            conditions.append(f"category = ${len(params) + 1}")
            params.append(category)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT product_id, product_name, category, suggested_price
                FROM analytics_varejo.dim_produtos
                {where}
                ORDER BY product_name
                LIMIT ${len(params)}
                """,
                params,
            )
            return [dict(row) async for row in rows]

    async def list_vendas(
        self,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if status:
            conditions.append(f"status = ${len(params) + 1}")
            params.append(status)
        if start_date:
            conditions.append(f"sale_date >= ${len(params) + 1}")
            params.append(start_date)
        if end_date:
            conditions.append(f"sale_date <= ${len(params) + 1}")
            params.append(end_date)
        if customer_id:
            conditions.append(f"customer_id = ${len(params) + 1}")
            params.append(customer_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT sale_id, customer_id, product_id, sale_date, status,
                       quantity, total_amount, recognized_revenue, refunded_amount
                FROM analytics_varejo.fct_vendas
                {where}
                ORDER BY sale_date DESC
                LIMIT ${len(params)}
                """,
                params,
            )
            return [dict(row) async for row in rows]

    async def get_dashboard(self) -> dict[str, Any]:
        async with self._pool.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    count(distinct customer_id)             as total_customers,
                    count(distinct product_id)              as total_products,
                    count(*)                                as total_sales,
                    sum(recognized_revenue)                 as total_revenue,
                    round(avg(total_amount)::numeric, 2)    as avg_sale_value,
                    sum(case when status='pago' then 1 end) as paid_sales,
                    sum(case when status='cancelado' then 1 end) as cancelled_sales,
                    sum(case when status='devolvido' then 1 end) as refunded_sales
                FROM analytics_varejo.fct_vendas
                """
            )
            return dict(row) if row else {}
