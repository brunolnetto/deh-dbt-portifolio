"""CRUD routes for the biblioteca (library) OLTP domain."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from ..database import get_pool

router = APIRouter(prefix="/biblioteca", tags=["biblioteca"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    tipo: str = "comum"


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None
    tipo: str | None = None


class LivroCreate(BaseModel):
    titulo: str
    isbn: str
    ano_publicacao: int
    quantidade_disponivel: int = 1


class LivroUpdate(BaseModel):
    titulo: str | None = None
    quantidade_disponivel: int | None = None


class EmprestimoCreate(BaseModel):
    usuario_id: int
    livro_id: int
    data_devolucao_prevista: str


class AutorCreate(BaseModel):
    nome: str
    nacionalidade: str
    data_nascimento: str | None = None


class AutorUpdate(BaseModel):
    nome: str | None = None
    nacionalidade: str | None = None


# ── helpers ───────────────────────────────────────────────────────────────────

async def _get_or_404(pool, table: str, id_col: str, id_val: int) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(f"SELECT * FROM {table} WHERE {id_col} = $1", [id_val])
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{table} id={id_val} não encontrado")
    return row


# ── usuarios ──────────────────────────────────────────────────────────────────

@router.get("/usuarios")
async def list_usuarios(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    tipo: str | None = None,
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    conditions, params = [], []
    if tipo:
        conditions.append(f"tipo = ${len(params) + 1}")
        params.append(tipo)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT * FROM biblioteca.usuario {where} "
                f"ORDER BY id LIMIT ${len(params) - 1} OFFSET ${len(params)}",
                params,
            )
            return await cur.fetchall()


@router.get("/usuarios/{usuario_id}")
async def get_usuario(usuario_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    return await _get_or_404(pool, "biblioteca.usuario", "id", usuario_id)


@router.post("/usuarios", status_code=201)
async def create_usuario(body: UsuarioCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO biblioteca.usuario (nome, email, tipo, data_cadastro, updated_at) "
                "VALUES ($1, $2, $3, now(), now()) RETURNING *",
                [body.nome, body.email.lower(), body.tipo],
            )
            return await cur.fetchone()


@router.put("/usuarios/{usuario_id}")
async def update_usuario(
    usuario_id: int, body: UsuarioUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE biblioteca.usuario SET {sets}, updated_at = now() WHERE id = $1 RETURNING *",
                [usuario_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return row


@router.delete("/usuarios/{usuario_id}", status_code=204)
async def delete_usuario(usuario_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> None:
    async with pool.connection() as conn:
        result = await conn.execute("DELETE FROM biblioteca.usuario WHERE id = $1", [usuario_id])
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")


# ── livros ────────────────────────────────────────────────────────────────────

@router.get("/livros")
async def list_livros(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM biblioteca.livro ORDER BY id LIMIT $1 OFFSET $2", [limit, offset]
            )
            return await cur.fetchall()


@router.get("/livros/{livro_id}")
async def get_livro(livro_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    return await _get_or_404(pool, "biblioteca.livro", "id", livro_id)


@router.post("/livros", status_code=201)
async def create_livro(body: LivroCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO biblioteca.livro (titulo, isbn, ano_publicacao, quantidade_disponivel, updated_at) "
                "VALUES ($1, $2, $3, $4, now()) RETURNING *",
                [body.titulo, body.isbn, body.ano_publicacao, body.quantidade_disponivel],
            )
            return await cur.fetchone()


@router.put("/livros/{livro_id}")
async def update_livro(
    livro_id: int, body: LivroUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE biblioteca.livro SET {sets}, updated_at = now() WHERE id = $1 RETURNING *",
                [livro_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    return row


@router.delete("/livros/{livro_id}", status_code=204)
async def delete_livro(livro_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> None:
    async with pool.connection() as conn:
        result = await conn.execute("DELETE FROM biblioteca.livro WHERE id = $1", [livro_id])
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Livro não encontrado")


# ── emprestimos ───────────────────────────────────────────────────────────────

@router.get("/emprestimos")
async def list_emprestimos(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    usuario_id: int | None = None,
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    conditions, params = [], []
    if usuario_id:
        conditions.append(f"usuario_id = ${len(params) + 1}")
        params.append(usuario_id)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT * FROM biblioteca.emprestimo {where} "
                f"ORDER BY id LIMIT ${len(params) - 1} OFFSET ${len(params)}",
                params,
            )
            return await cur.fetchall()


@router.get("/emprestimos/{emprestimo_id}")
async def get_emprestimo(emprestimo_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    return await _get_or_404(pool, "biblioteca.emprestimo", "id", emprestimo_id)


@router.post("/emprestimos", status_code=201)
async def create_emprestimo(body: EmprestimoCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO biblioteca.emprestimo "
                "(usuario_id, livro_id, data_emprestimo, data_devolucao_prevista, updated_at) "
                "VALUES ($1, $2, current_date, $3::date, now()) RETURNING *",
                [body.usuario_id, body.livro_id, body.data_devolucao_prevista],
            )
            return await cur.fetchone()


@router.delete("/emprestimos/{emprestimo_id}", status_code=204)
async def delete_emprestimo(emprestimo_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> None:
    async with pool.connection() as conn:
        result = await conn.execute("DELETE FROM biblioteca.emprestimo WHERE id = $1", [emprestimo_id])
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")


# ── multas ────────────────────────────────────────────────────────────────────

@router.get("/multas")
async def list_multas(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM biblioteca.multa ORDER BY id LIMIT $1 OFFSET $2", [limit, offset]
            )
            return await cur.fetchall()


# ── autores ───────────────────────────────────────────────────────────────────

@router.get("/autores")
async def list_autores(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM biblioteca.autor ORDER BY id LIMIT $1 OFFSET $2", [limit, offset]
            )
            return await cur.fetchall()


@router.get("/autores/{autor_id}")
async def get_autor(autor_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    return await _get_or_404(pool, "biblioteca.autor", "id", autor_id)


@router.post("/autores", status_code=201)
async def create_autor(body: AutorCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO biblioteca.autor (nome, nacionalidade, data_nascimento, updated_at) "
                "VALUES ($1, $2, $3::date, now()) RETURNING *",
                [body.nome, body.nacionalidade, body.data_nascimento],
            )
            return await cur.fetchone()


@router.put("/autores/{autor_id}")
async def update_autor(
    autor_id: int, body: AutorUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE biblioteca.autor SET {sets}, updated_at = now() WHERE id = $1 RETURNING *",
                [autor_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Autor não encontrado")
    return row
