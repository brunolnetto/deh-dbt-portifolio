from typing import Any

from fastapi import APIRouter, Depends, Query

from ...infrastructure.database import get_pool
from ...infrastructure.biblioteca.repository import BibliotecaRepository

router = APIRouter()


def _repo() -> BibliotecaRepository:
    return BibliotecaRepository(get_pool())


@router.get("/livros", summary="Listar livros do acervo")
async def list_livros(
    available_only: bool = Query(False, description="Apenas livros disponíveis para empréstimo"),
    limit: int = Query(50, le=500),
    repo: BibliotecaRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_livros(available_only=available_only, limit=limit)


@router.get("/usuarios", summary="Listar usuários da biblioteca")
async def list_usuarios(
    user_type: str | None = Query(None, description="aluno | professor"),
    limit: int = Query(50, le=500),
    repo: BibliotecaRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_usuarios(user_type=user_type, limit=limit)


@router.get("/emprestimos", summary="Listar empréstimos")
async def list_emprestimos(
    is_overdue: bool | None = Query(None, description="Filtrar apenas atrasados"),
    usuario_id: int | None = Query(None),
    limit: int = Query(50, le=500),
    repo: BibliotecaRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    return await repo.list_emprestimos(
        is_overdue=is_overdue,
        usuario_id=usuario_id,
        limit=limit,
    )


@router.get("/dashboard", summary="Métricas consolidadas da biblioteca")
async def get_dashboard(
    repo: BibliotecaRepository = Depends(_repo),
) -> dict[str, Any]:
    return await repo.get_dashboard()
