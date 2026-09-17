"""Great Expectations validation for landing tables — using pandas assertions."""
import os
from typing import Any

import pandas as pd
import psycopg
import pytest

from .conftest import POSTGRES_DSN


def _load(schema: str, table: str) -> pd.DataFrame:
    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {schema}.{table}")
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
    return pd.DataFrame(rows, columns=cols)


def test_ge_clientes():
    """Validate landing_varejo.clientes — row count, nulls, uniqueness."""
    df = _load("landing_varejo", "clientes")
    assert len(df) > 0, "clientes: row count must be > 0"
    assert df['cliente_id'].notna().all(), "clientes: cliente_id contains NULLs"
    assert df['cliente_id'].is_unique, "clientes: cliente_id is not unique"
    assert df['nome'].notna().all(), "clientes: nome contains NULLs"


def test_ge_produtos():
    """Validate landing_varejo.produtos — row count, nulls, uniqueness, price range."""
    df = _load("landing_varejo", "produtos")
    assert len(df) > 0, "produtos: row count must be > 0"
    assert df['produto_id'].notna().all(), "produtos: produto_id contains NULLs"
    assert df['produto_id'].is_unique, "produtos: produto_id is not unique"
    assert (df['preco_sugerido'] >= 0).all(), "produtos: preco_sugerido has negative values"


def test_ge_vendas():
    """Validate landing_varejo.vendas — row count, required columns non-null."""
    df = _load("landing_varejo", "vendas")
    assert len(df) > 0, "vendas: row count must be > 0"
    assert df['venda_id'].notna().all(), "vendas: venda_id contains NULLs"
    assert df['cliente_id'].notna().all(), "vendas: cliente_id contains NULLs"
    assert df['produto_id'].notna().all(), "vendas: produto_id contains NULLs"


def test_ge_usuarios():
    """Validate landing_biblioteca.usuarios — row count, nulls, uniqueness."""
    df = _load("landing_biblioteca", "usuarios")
    assert len(df) > 0, "usuarios: row count must be > 0"
    assert df['usuario_id'].notna().all(), "usuarios: usuario_id contains NULLs"
    assert df['usuario_id'].is_unique, "usuarios: usuario_id is not unique"


def test_ge_emprestimos():
    """Validate landing_biblioteca.emprestimos — row count, required columns non-null."""
    df = _load("landing_biblioteca", "emprestimos")
    assert len(df) > 0, "emprestimos: row count must be > 0"
    assert df['emprestimo_id'].notna().all(), "emprestimos: emprestimo_id contains NULLs"
    assert df['usuario_id'].notna().all(), "emprestimos: usuario_id contains NULLs"
    assert df['livro_id'].notna().all(), "emprestimos: livro_id contains NULLs"


def test_ge_pessoas():
    """Validate landing_rede_social.pessoas — row count, nulls, uniqueness."""
    df = _load("landing_rede_social", "pessoas")
    assert len(df) > 0, "pessoas: row count must be > 0"
    assert df['pessoa_id'].notna().all(), "pessoas: pessoa_id contains NULLs"
    assert df['pessoa_id'].is_unique, "pessoas: pessoa_id is not unique"
