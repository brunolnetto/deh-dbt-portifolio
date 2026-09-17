"""CRUD routes for the rede_social (social reading network) OLTP domain."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from ..database import get_pool

router = APIRouter(prefix="/rede_social", tags=["rede_social"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class PessoaCreate(BaseModel):
    nome: str
    idade: int


class PessoaUpdate(BaseModel):
    nome: str | None = None
    idade: int | None = None


class LeituraCreate(BaseModel):
    pessoa_id: int
    livro_id: int
    nota: float
    data_leitura: str


class LeituraUpdate(BaseModel):
    nota: float | None = None


class ConexaoCreate(BaseModel):
    seguidor_id: int
    seguido_id: int
    forca_conexao: float = 5.0


class LivroRedeSocialCreate(BaseModel):
    titulo: str
    autor: str
    ano_publicacao: int | None = None


# ── helpers ───────────────────────────────────────────────────────────────────

async def _get_or_404(pool, table: str, id_col: str, id_val: int) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(f"SELECT * FROM {table} WHERE {id_col} = $1", [id_val])
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{table} id={id_val} não encontrado")
    return row


# ── pessoas ───────────────────────────────────────────────────────────────────

@router.get("/pessoas")
async def list_pessoas(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM rede_social.pessoa ORDER BY id LIMIT $1 OFFSET $2", [limit, offset]
            )
            return await cur.fetchall()


@router.get("/pessoas/{pessoa_id}")
async def get_pessoa(pessoa_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    return await _get_or_404(pool, "rede_social.pessoa", "id", pessoa_id)


@router.post("/pessoas", status_code=201)
async def create_pessoa(body: PessoaCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO rede_social.pessoa (nome, idade, updated_at) "
                "VALUES ($1, $2, now()) RETURNING *",
                [body.nome, body.idade],
            )
            return await cur.fetchone()


@router.put("/pessoas/{pessoa_id}")
async def update_pessoa(
    pessoa_id: int, body: PessoaUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE rede_social.pessoa SET {sets}, updated_at = now() WHERE id = $1 RETURNING *",
                [pessoa_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return row


@router.delete("/pessoas/{pessoa_id}", status_code=204)
async def delete_pessoa(pessoa_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> None:
    async with pool.connection() as conn:
        result = await conn.execute("DELETE FROM rede_social.pessoa WHERE id = $1", [pessoa_id])
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")


# ── leituras ──────────────────────────────────────────────────────────────────

@router.get("/leituras")
async def list_leituras(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pessoa_id: int | None = None,
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    conditions, params = [], []
    if pessoa_id:
        conditions.append(f"pessoa_id = ${len(params) + 1}")
        params.append(pessoa_id)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT * FROM rede_social.leitura {where} "
                f"ORDER BY id LIMIT ${len(params) - 1} OFFSET ${len(params)}",
                params,
            )
            return await cur.fetchall()


@router.get("/leituras/{leitura_id}")
async def get_leitura(leitura_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    return await _get_or_404(pool, "rede_social.leitura", "id", leitura_id)


@router.post("/leituras", status_code=201)
async def create_leitura(body: LeituraCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO rede_social.leitura (pessoa_id, livro_id, nota, data_leitura, updated_at) "
                "VALUES ($1, $2, $3, $4::date, now()) RETURNING *",
                [body.pessoa_id, body.livro_id, body.nota, body.data_leitura],
            )
            return await cur.fetchone()


@router.put("/leituras/{leitura_id}")
async def update_leitura(
    leitura_id: int, body: LeituraUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE rede_social.leitura SET {sets}, updated_at = now() WHERE id = $1 RETURNING *",
                [leitura_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Leitura não encontrada")
    return row


@router.delete("/leituras/{leitura_id}", status_code=204)
async def delete_leitura(leitura_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> None:
    async with pool.connection() as conn:
        result = await conn.execute("DELETE FROM rede_social.leitura WHERE id = $1", [leitura_id])
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Leitura não encontrada")


# ── conexoes ──────────────────────────────────────────────────────────────────

@router.get("/conexoes")
async def list_conexoes(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM rede_social.conexao_social ORDER BY id LIMIT $1 OFFSET $2", [limit, offset]
            )
            return await cur.fetchall()


@router.post("/conexoes", status_code=201)
async def create_conexao(body: ConexaoCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO rede_social.conexao_social "
                "(seguidor_id, seguido_id, forca_conexao, data_conexao, updated_at) "
                "VALUES ($1, $2, $3, current_date, now()) RETURNING *",
                [body.seguidor_id, body.seguido_id, body.forca_conexao],
            )
            return await cur.fetchone()


@router.delete("/conexoes/{conexao_id}", status_code=204)
async def delete_conexao(conexao_id: int, pool: AsyncConnectionPool = Depends(get_pool)) -> None:
    async with pool.connection() as conn:
        result = await conn.execute("DELETE FROM rede_social.conexao_social WHERE id = $1", [conexao_id])
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")


# ── generos ───────────────────────────────────────────────────────────────────

@router.get("/generos")
async def list_generos(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM rede_social.genero ORDER BY id LIMIT $1 OFFSET $2", [limit, offset]
            )
            return await cur.fetchall()


# ── livros (rede_social) ──────────────────────────────────────────────────────

@router.get("/livros")
async def list_livros(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM rede_social.livro ORDER BY id LIMIT $1 OFFSET $2", [limit, offset]
            )
            return await cur.fetchall()


@router.post("/livros", status_code=201)
async def create_livro(body: LivroRedeSocialCreate, pool: AsyncConnectionPool = Depends(get_pool)) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO rede_social.livro (titulo, autor, ano_publicacao, updated_at) "
                "VALUES ($1, $2, $3, now()) RETURNING *",
                [body.titulo, body.autor, body.ano_publicacao],
            )
            return await cur.fetchone()
