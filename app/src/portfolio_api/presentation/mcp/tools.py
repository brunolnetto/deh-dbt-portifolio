"""MCP tools for the Portfolio Analytics API.

Covers all 3 domains: varejo, biblioteca, rede_social.
Mount in FastAPI: app.mount("/mcp", mcp.streamable_http_app())
"""

import json
from contextlib import asynccontextmanager
from datetime import date

from mcp.server.mcpserver import MCPServer

from ...config import settings
from ...infrastructure.database import close_pool, get_pool, init_pool
from ...infrastructure.varejo.repository import VarejoRepository
from ...infrastructure.biblioteca.repository import BibliotecaRepository
from ...infrastructure.rede_social.repository import RedeSocialRepository


@asynccontextmanager
async def _lifespan(server: MCPServer):  # noqa: ARG001
    await init_pool(settings.db_dsn)
    yield
    await close_pool()


mcp = MCPServer(
    "portfolio-analytics",
    instructions=(
        "Query the DEH Portfolio Analytics warehouse. "
        "Three domains: varejo (retail), biblioteca (library), rede_social (social reading network). "
        "All data is read from analytics schemas built by dbt. "
        "Dates must be ISO 8601 strings (YYYY-MM-DD)."
    ),
    lifespan=_lifespan,
)


def _json(obj) -> str:
    return json.dumps(obj, default=str, indent=2)


def _iso(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


# ── VAREJO ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_varejo_dashboard(
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Aggregate retail (varejo) metrics: total sales, revenue, paid/cancelled/refunded counts."""
    repo = VarejoRepository(get_pool())
    result = await repo.get_dashboard()
    return _json(result)


@mcp.tool()
async def list_varejo_clientes(
    state: str | None = None,
    segment: str | None = None,
    limit: int = 20,
) -> str:
    """List retail customers. Filter by Brazilian state code (SP, RJ…) or segment (Ouro/Prata/Bronze)."""
    repo = VarejoRepository(get_pool())
    result = await repo.list_clientes(state=state, segment=segment, limit=limit)
    return _json(result)


@mcp.tool()
async def list_varejo_vendas(
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_id: int | None = None,
    limit: int = 20,
) -> str:
    """List retail sales. Status: pago | cancelado | devolvido | pendente."""
    repo = VarejoRepository(get_pool())
    result = await repo.list_vendas(
        status=status,
        start_date=_iso(start_date),
        end_date=_iso(end_date),
        customer_id=customer_id,
        limit=limit,
    )
    return _json(result)


# ── BIBLIOTECA ────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_biblioteca_dashboard() -> str:
    """Aggregate library (biblioteca) metrics: total books, active loans, overdue count, fines."""
    repo = BibliotecaRepository(get_pool())
    result = await repo.get_dashboard()
    return _json(result)


@mcp.tool()
async def list_biblioteca_livros(
    available_only: bool = False,
    limit: int = 20,
) -> str:
    """List library books. Set available_only=true to see only books available for loan."""
    repo = BibliotecaRepository(get_pool())
    result = await repo.list_livros(available_only=available_only, limit=limit)
    return _json(result)


@mcp.tool()
async def list_biblioteca_emprestimos(
    is_overdue: bool | None = None,
    usuario_id: int | None = None,
    limit: int = 20,
) -> str:
    """List loan records. is_overdue=true shows only late returns."""
    repo = BibliotecaRepository(get_pool())
    result = await repo.list_emprestimos(
        is_overdue=is_overdue,
        usuario_id=usuario_id,
        limit=limit,
    )
    return _json(result)


# ── REDE SOCIAL ───────────────────────────────────────────────────────────────

@mcp.tool()
async def get_rede_social_dashboard() -> str:
    """Aggregate social reading network metrics: total people, books, readings, connections."""
    repo = RedeSocialRepository(get_pool())
    result = await repo.get_dashboard()
    return _json(result)


@mcp.tool()
async def get_book_recommendations(pessoa_id: int) -> str:
    """
    Get personalized book recommendations for a person based on their social connections.
    Returns books read by the people they follow, ranked by network avg_rating.
    """
    repo = RedeSocialRepository(get_pool())
    result = await repo.get_recomendacoes(pessoa_id)
    return _json(result)


@mcp.tool()
async def list_rede_social_leituras(
    pessoa_id: int | None = None,
    limit: int = 20,
) -> str:
    """List reading records from the social network. Filter by pessoa_id to see one person's history."""
    repo = RedeSocialRepository(get_pool())
    result = await repo.list_leituras(pessoa_id=pessoa_id, limit=limit)
    return _json(result)
