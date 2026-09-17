"""CRUD routes for the varejo (retail) OLTP domain."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from ..database import get_pool

router = APIRouter(prefix="/varejo", tags=["varejo"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class ClienteCreate(BaseModel):
    nome: str
    estado: str
    segmento: str


class ClienteUpdate(BaseModel):
    nome: str | None = None
    estado: str | None = None
    segmento: str | None = None


class ProdutoCreate(BaseModel):
    nome_produto: str
    categoria: str
    preco_sugerido: float


class ProdutoUpdate(BaseModel):
    nome_produto: str | None = None
    categoria: str | None = None
    preco_sugerido: float | None = None


class VendaCreate(BaseModel):
    cliente_id: int
    produto_id: int
    quantidade: int
    valor_total: float
    status: str = "pendente"


class VendaUpdate(BaseModel):
    status: str | None = None
    quantidade: int | None = None
    valor_total: float | None = None


# ── clientes ──────────────────────────────────────────────────────────────────

@router.get("/clientes")
async def list_clientes(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    estado: str | None = None,
    segmento: str | None = None,
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    conditions, params = [], []
    if estado:
        conditions.append(f"estado = ${len(params) + 1}")
        params.append(estado.upper())
    if segmento:
        conditions.append(f"segmento = ${len(params) + 1}")
        params.append(segmento)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT * FROM varejo.origem_cliente {where} "
                f"ORDER BY id LIMIT ${len(params) - 1} OFFSET ${len(params)}",
                params,
            )
            return await cur.fetchall()


@router.get("/clientes/{cliente_id}")
async def get_cliente(
    cliente_id: int, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM varejo.origem_cliente WHERE id = $1", [cliente_id]
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return row


@router.post("/clientes", status_code=201)
async def create_cliente(
    body: ClienteCreate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO varejo.origem_cliente (nome, estado, segmento, data_cadastro, updated_at) "
                "VALUES ($1, $2, $3, now(), now()) RETURNING *",
                [body.nome, body.estado.upper(), body.segmento],
            )
            return await cur.fetchone()


@router.put("/clientes/{cliente_id}")
async def update_cliente(
    cliente_id: int, body: ClienteUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE varejo.origem_cliente SET {sets}, updated_at = now() "
                f"WHERE id = $1 RETURNING *",
                [cliente_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return row


@router.delete("/clientes/{cliente_id}", status_code=204)
async def delete_cliente(
    cliente_id: int, pool: AsyncConnectionPool = Depends(get_pool)
) -> None:
    async with pool.connection() as conn:
        result = await conn.execute(
            "DELETE FROM varejo.origem_cliente WHERE id = $1", [cliente_id]
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


# ── produtos ──────────────────────────────────────────────────────────────────

@router.get("/produtos")
async def list_produtos(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    categoria: str | None = None,
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    conditions, params = [], []
    if categoria:
        conditions.append(f"categoria = ${len(params) + 1}")
        params.append(categoria)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT * FROM varejo.origem_produto {where} "
                f"ORDER BY id LIMIT ${len(params) - 1} OFFSET ${len(params)}",
                params,
            )
            return await cur.fetchall()


@router.get("/produtos/{produto_id}")
async def get_produto(
    produto_id: int, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM varejo.origem_produto WHERE id = $1", [produto_id]
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return row


@router.post("/produtos", status_code=201)
async def create_produto(
    body: ProdutoCreate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO varejo.origem_produto "
                "(nome_produto, categoria, preco_sugerido, updated_at) "
                "VALUES ($1, $2, $3, now()) RETURNING *",
                [body.nome_produto, body.categoria, body.preco_sugerido],
            )
            return await cur.fetchone()


@router.put("/produtos/{produto_id}")
async def update_produto(
    produto_id: int, body: ProdutoUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE varejo.origem_produto SET {sets}, updated_at = now() "
                f"WHERE id = $1 RETURNING *",
                [produto_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return row


@router.delete("/produtos/{produto_id}", status_code=204)
async def delete_produto(
    produto_id: int, pool: AsyncConnectionPool = Depends(get_pool)
) -> None:
    async with pool.connection() as conn:
        result = await conn.execute(
            "DELETE FROM varejo.origem_produto WHERE id = $1", [produto_id]
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Produto não encontrado")


# ── vendas ────────────────────────────────────────────────────────────────────

@router.get("/vendas")
async def list_vendas(
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    cliente_id: int | None = None,
    pool: AsyncConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    conditions, params = [], []
    if status:
        conditions.append(f"status = ${len(params) + 1}")
        params.append(status)
    if cliente_id:
        conditions.append(f"cliente_id = ${len(params) + 1}")
        params.append(cliente_id)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params += [limit, offset]
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"SELECT * FROM varejo.origem_venda {where} "
                f"ORDER BY id LIMIT ${len(params) - 1} OFFSET ${len(params)}",
                params,
            )
            return await cur.fetchall()


@router.get("/vendas/{venda_id}")
async def get_venda(
    venda_id: int, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT * FROM varejo.origem_venda WHERE id = $1", [venda_id]
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return row


@router.post("/vendas", status_code=201)
async def create_venda(
    body: VendaCreate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "INSERT INTO varejo.origem_venda "
                "(cliente_id, produto_id, quantidade, valor_total, status, data_venda, created_at, updated_at) "
                "VALUES ($1, $2, $3, $4, $5, current_date, now(), now()) RETURNING *",
                [body.cliente_id, body.produto_id, body.quantidade, body.valor_total, body.status],
            )
            return await cur.fetchone()


@router.put("/vendas/{venda_id}")
async def update_venda(
    venda_id: int, body: VendaUpdate, pool: AsyncConnectionPool = Depends(get_pool)
) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    sets = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                f"UPDATE varejo.origem_venda SET {sets}, updated_at = now() "
                f"WHERE id = $1 RETURNING *",
                [venda_id, *updates.values()],
            )
            row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return row


@router.delete("/vendas/{venda_id}", status_code=204)
async def delete_venda(
    venda_id: int, pool: AsyncConnectionPool = Depends(get_pool)
) -> None:
    async with pool.connection() as conn:
        result = await conn.execute(
            "DELETE FROM varejo.origem_venda WHERE id = $1", [venda_id]
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
