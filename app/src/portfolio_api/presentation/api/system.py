"""System domain REST endpoints — request logs and API health."""
from typing import Any

from fastapi import APIRouter, Depends, Query

from ...infrastructure.database import get_pool
from ...infrastructure.system.repository import SystemRepository

router = APIRouter()


def _repo() -> SystemRepository:
    return SystemRepository(get_pool())


@router.get("/requests", summary="Listar logs de requisições (paginado)")
async def list_requests(
    service: str | None = Query(None, description="Filtrar por serviço (ex: oltp-api)"),
    errors_only: bool = Query(False, description="Apenas requisições com status >= 400"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=500),
    repo: SystemRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_requests(
        service=service,
        status_gte=400 if errors_only else None,
        page=page,
        per_page=per_page,
    )


@router.get("/health", summary="Saúde da API por janela de tempo")
async def get_api_health(
    repo: SystemRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.get_api_health()
