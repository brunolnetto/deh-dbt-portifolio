from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from ...infrastructure.database import get_pool
from ...infrastructure.varejo.repository import VarejoRepository

router = APIRouter()


def _repo() -> VarejoRepository:
    return VarejoRepository(get_pool())


@router.get("/clientes", summary="Listar clientes do varejo")
async def list_clientes(
    state: str | None = Query(None, description="Sigla do estado (ex: SP)"),
    segment: str | None = Query(None, description="Ouro | Prata | Bronze"),
    limit: int = Query(50, le=500),
    repo: VarejoRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_clientes(state=state, segment=segment, limit=limit)


@router.get("/produtos", summary="Listar produtos do catálogo")
async def list_produtos(
    category: str | None = Query(None, description="Categoria do produto"),
    limit: int = Query(50, le=500),
    repo: VarejoRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_produtos(category=category, limit=limit)


@router.get("/vendas", summary="Listar transações de venda")
async def list_vendas(
    status: str | None = Query(None, description="pago | cancelado | devolvido | pendente"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    customer_id: int | None = Query(None),
    limit: int = Query(50, le=500),
    repo: VarejoRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_vendas(
        status=status,
        start_date=start_date,
        end_date=end_date,
        customer_id=customer_id,
        limit=limit,
    )


@router.get("/dashboard", summary="Métricas consolidadas do varejo")
async def get_dashboard(
    repo: VarejoRepository = Depends(_repo),
) -> dict[str, Any]:
    return await repo.get_dashboard()
