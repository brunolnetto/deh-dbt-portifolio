"""FastAPI Portfolio API — REST + MCP (Streamable HTTP at /mcp).

Domains:
  - /api/v1/varejo       → retail analytics
  - /api/v1/biblioteca   → library analytics
  - /api/v1/rede_social  → social reading network analytics
  - /mcp                 → MCP Streamable HTTP transport
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .infrastructure.database import close_pool, init_pool
from .presentation.api.varejo import router as varejo_router
from .presentation.api.biblioteca import router as biblioteca_router
from .presentation.api.rede_social import router as rede_social_router
from .presentation.mcp.tools import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await init_pool(settings.db_dsn)
    yield
    await close_pool()


app = FastAPI(
    title="DEH Portfolio Analytics API",
    description=(
        "REST and MCP interface over the DEH Portfolio Analytics warehouse.\n\n"
        "**Domains:** varejo · biblioteca · rede_social\n\n"
        "**MCP endpoint:** `POST /mcp` (Streamable HTTP transport)"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(varejo_router,      prefix="/api/v1/varejo",      tags=["varejo"])
app.include_router(biblioteca_router,  prefix="/api/v1/biblioteca",  tags=["biblioteca"])
app.include_router(rede_social_router, prefix="/api/v1/rede_social", tags=["rede_social"])

app.mount("/mcp", mcp.streamable_http_app())
