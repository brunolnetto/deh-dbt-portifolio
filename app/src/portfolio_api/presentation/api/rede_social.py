from typing import Any

from fastapi import APIRouter, Depends, Path, Query

from ...infrastructure.database import get_pool
from ...infrastructure.rede_social.repository import RedeSocialRepository

router = APIRouter()


def _repo() -> RedeSocialRepository:
    return RedeSocialRepository(get_pool())


@router.get("/pessoas", summary="Listar pessoas da rede social")
async def list_pessoas(
    limit: int = Query(50, le=500),
    repo: RedeSocialRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_pessoas(limit=limit)


@router.get("/leituras", summary="Listar registros de leitura")
async def list_leituras(
    pessoa_id: int | None = Query(None),
    livro_id: int | None = Query(None),
    limit: int = Query(50, le=500),
    repo: RedeSocialRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_leituras(
        pessoa_id=pessoa_id,
        livro_id=livro_id,
        limit=limit,
    )


@router.get(
    "/recomendacoes/{pessoa_id}",
    summary="Recomendações de livros baseadas na rede de conexões",
)
async def get_recomendacoes(
    pessoa_id: int = Path(..., description="ID da pessoa"),
    repo: RedeSocialRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.get_recomendacoes(pessoa_id)


@router.get("/dashboard", summary="Métricas consolidadas da rede social")
async def get_dashboard(
    repo: RedeSocialRepository = Depends(_repo),
) -> dict[str, Any]:
    return await repo.get_dashboard()
