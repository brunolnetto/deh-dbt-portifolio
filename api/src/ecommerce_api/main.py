"""FastAPI application — REST + MCP (Streamable HTTP at /mcp)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .infrastructure.database import close_pool, init_pool
from .presentation.api.orders import router as orders_router
from .presentation.api.products import router as products_router
from .presentation.api.salespeople import router as salespeople_router
from .presentation.mcp.tools import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await init_pool(settings.db_dsn)
    yield
    await close_pool()


app = FastAPI(
    title="Ecommerce Analytics API",
    description=(
        "REST and MCP interface over the dbt ecommerce analytics layer.\n\n"
        "**MCP endpoint:** `POST /mcp` (Streamable HTTP transport)"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(orders_router,      prefix="/api/v1/orders",      tags=["orders"])
app.include_router(products_router,    prefix="/api/v1/products",    tags=["products"])
app.include_router(salespeople_router, prefix="/api/v1/salespeople", tags=["salespeople"])

# MCP Streamable HTTP transport — accepts POST /mcp from any MCP client
app.mount("/mcp", mcp.streamable_http_app())
