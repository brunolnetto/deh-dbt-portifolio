"""System domain queries — request logs and API health analytics."""
from typing import Any

from psycopg_pool import AsyncConnectionPool


class SystemRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_requests(
        self,
        service: str | None = None,
        status_gte: int | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if service:
            conditions.append(f"service = ${len(params) + 1}")
            params.append(service)
        if status_gte:
            conditions.append(f"status_code >= ${len(params) + 1}")
            params.append(status_gte)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (page - 1) * per_page
        params += [per_page, offset]

        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT id, service, method, endpoint, status_code, duration_ms, created_at
                FROM system.request_log
                {where}
                ORDER BY created_at DESC
                LIMIT ${len(params) - 1} OFFSET ${len(params)}
                """,
                params,
            )
            return [dict(row) async for row in rows]

    async def get_api_health(self) -> list[dict[str, Any]]:
        async with self._pool.connection() as conn:
            rows = await conn.execute(
                """
                SELECT service, window_start, total_requests, error_requests,
                       avg_duration_ms, p95_duration_ms, error_rate_pct
                FROM analytics_system.mart_api_health
                ORDER BY window_start DESC
                LIMIT 48
                """
            )
            return [dict(row) async for row in rows]
