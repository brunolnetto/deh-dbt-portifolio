"""MCP tools — one tool per semantic-layer metric group.

Tool naming mirrors the semantic model names defined in:
  ecommerce/models/semantic/semantic_orders.yml
  ecommerce/models/semantic/semantic_products.yml
  ecommerce/models/semantic/semantic_salespeople.yml

Run standalone:   python -m ecommerce_api.mcp_server
Mount in FastAPI: app.mount("/mcp", mcp.streamable_http_app())
"""

import json
from contextlib import asynccontextmanager
from datetime import date

from mcp.server.mcpserver import MCPServer

from ...config import settings
from ...infrastructure.database import close_pool, init_pool, get_pool
from ...infrastructure.orders.repository import PostgresOrderRepository
from ...infrastructure.products.repository import PostgresProductRepository
from ...infrastructure.salespeople.repository import PostgresSalespersonRepository
from ...application.orders.queries import OrderQueries
from ...application.products.queries import ProductQueries
from ...application.salespeople.queries import SalespersonQueries


@asynccontextmanager
async def _lifespan(server: MCPServer):  # noqa: ARG001
    await init_pool(settings.db_dsn)
    yield
    await close_pool()


mcp = MCPServer(
    "ecommerce-analytics",
    instructions=(
        "Query the ecommerce analytics warehouse built with dbt. "
        "All data is read from the analytics schema (mart layer). "
        "Dates must be ISO 8601 strings (YYYY-MM-DD)."
    ),
    lifespan=_lifespan,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _orders() -> OrderQueries:
    return OrderQueries(PostgresOrderRepository(get_pool()))


def _products() -> ProductQueries:
    return ProductQueries(PostgresProductRepository(get_pool()))


def _salespeople() -> SalespersonQueries:
    return SalespersonQueries(PostgresSalespersonRepository(get_pool()))


def _iso(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _json(obj) -> str:
    return json.dumps(obj, default=str, indent=2)


# ── semantic_orders.yml ──────────────────────────────────────────────────────


@mcp.tool()
async def get_order_metrics(
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
) -> str:
    """
    Aggregate order metrics from fct_orders.

    Returns: order_count, purchaser_count, gross_merchandise_value, revenue,
    paid_orders, refunded_orders, refund_amount, average_order_value,
    refund_rate, refund_amount_ratio.

    status: pending | paid | cancelled | refunded (omit for all).
    """
    m = await _orders().get_metrics(
        status=status,
        start_date=_iso(start_date),
        end_date=_iso(end_date),
    )
    return _json(m.model_dump(mode="json"))


@mcp.tool()
async def list_orders(
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_id: int | None = None,
    salesperson_id: int | None = None,
    limit: int = 20,
) -> str:
    """
    List individual orders with optional filters.
    Returns order_id, customer, salesperson, date, status, amount, revenue.
    """
    orders = await _orders().list_orders(
        status=status,
        start_date=_iso(start_date),
        end_date=_iso(end_date),
        customer_id=customer_id,
        salesperson_id=salesperson_id,
        limit=limit,
    )
    return _json([o.model_dump(mode="json") for o in orders])


# ── semantic_products.yml ────────────────────────────────────────────────────


@mcp.tool()
async def get_product_metrics(
    product_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    Aggregate product metrics from fct_order_items.

    Returns: items_sold, product_revenue, average_unit_price.
    Pass product_id to scope to one product.
    """
    m = await _products().get_metrics(
        product_id=product_id,
        start_date=_iso(start_date),
        end_date=_iso(end_date),
    )
    return _json(m.model_dump(mode="json"))


@mcp.tool()
async def get_product_performance(
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 20,
) -> str:
    """
    Per-product breakdown: items_sold, product_revenue, average_unit_price.
    Ordered by revenue descending. Filter by category if needed.
    """
    rows = await _products().get_performance(
        category=category,
        start_date=_iso(start_date),
        end_date=_iso(end_date),
        limit=limit,
    )
    return _json([r.model_dump(mode="json") for r in rows])


@mcp.tool()
async def list_products(
    category: str | None = None,
    is_active: bool | None = None,
    limit: int = 50,
) -> str:
    """
    List products from the product dimension.
    Returns product_id, name, category, unit_price, is_active.
    """
    products = await _products().list_products(
        category=category,
        is_active=is_active,
        limit=limit,
    )
    return _json([p.model_dump(mode="json") for p in products])


# ── semantic_salespeople.yml ─────────────────────────────────────────────────


@mcp.tool()
async def get_salesperson_metrics(
    salesperson_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    Salesperson performance metrics from fct_orders.

    Returns: salesperson_orders, salesperson_paid_orders,
    salesperson_refunded_orders, salesperson_revenue, salesperson_gmv,
    salesperson_average_order_value, salesperson_refund_rate.

    Omit salesperson_id for company-wide aggregate.
    """
    m = await _salespeople().get_metrics(
        salesperson_id=salesperson_id,
        start_date=_iso(start_date),
        end_date=_iso(end_date),
    )
    return _json(m.model_dump(mode="json"))


@mcp.tool()
async def list_salespeople() -> str:
    """List all salespeople: salesperson_id, name, region, email."""
    people = await _salespeople().list_salespeople()
    return _json([p.model_dump(mode="json") for p in people])
