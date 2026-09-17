"""FastAPI OLTP API — standard CRUD for all 3 domains."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .database import close_pool, init_pool
from .middleware import RequestLogMiddleware
from .routes import biblioteca, rede_social, varejo


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await init_pool(settings.db_dsn)
    yield
    await close_pool()


app = FastAPI(
    title="DEH Portfolio OLTP API",
    description="Standard CRUD interface over the 3-domain OLTP PostgreSQL database.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLogMiddleware)

app.include_router(varejo.router)
app.include_router(biblioteca.router)
app.include_router(rede_social.router)
