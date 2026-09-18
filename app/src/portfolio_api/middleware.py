"""Request-logging middleware for the Analytics API.

Writes one row to system.request_log per request, asynchronously,
without blocking the response path. Mirrors oltp_api.middleware so both
APIs feed the same system.request_log table consumed by dbt
(stg_request_logs -> mart_api_health).
"""
import asyncio
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .infrastructure.database import get_pool

log = logging.getLogger(__name__)

SERVICE = "analytics-api"


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        asyncio.create_task(
            _persist(request.method, request.url.path, response.status_code, duration_ms)
        )
        return response


async def _persist(method: str, endpoint: str, status_code: int, duration_ms: float) -> None:
    try:
        async with get_pool().connection() as conn:
            await conn.execute(
                "INSERT INTO system.request_log "
                "(service, method, endpoint, status_code, duration_ms) "
                "VALUES (%s, %s, %s, %s, %s)",
                [SERVICE, method, endpoint, status_code, duration_ms],
            )
    except Exception as exc:  # never let logging break the API
        log.debug("request_log write failed: %s", exc)
