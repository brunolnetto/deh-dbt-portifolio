"""Great Expectations validation for landing tables using the GE v1 Pandas-based API."""
import os
from typing import Any

import great_expectations as gx
import pandas as pd
import psycopg
import pytest
from great_expectations.expectations import (
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeGreaterThan,
)

from conftest import POSTGRES_DSN


def _load(schema: str, table: str) -> pd.DataFrame:
    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {schema}.{table}")
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
    return pd.DataFrame(rows, columns=cols)


def _run_suite(df: pd.DataFrame, name: str, expectations: list[Any]) -> None:
    ctx = gx.get_context()
    ds = ctx.data_sources.add_pandas(name=f"ds_{name}")
    asset = ds.add_dataframe_asset(name=name)
    batch_def = asset.add_batch_definition_whole_dataframe("batch")
    suite = ctx.suites.add(gx.ExpectationSuite(name=name))
    for exp in expectations:
        suite.add_expectation(exp)
    vdef = ctx.validation_definitions.add(
        gx.ValidationDefinition(name=name, data=batch_def, suite=suite)
    )
    result = vdef.run(batch_parameters={"dataframe": df})
    assert result.success, f"GE suite '{name}' failed:\n{result}"


def test_ge_clientes():
    _run_suite(
        _load("landing_varejo", "clientes"),
        "clientes",
        [
            ExpectTableRowCountToBeGreaterThan(value=0),
            ExpectColumnValuesToNotBeNull(column="cliente_id"),
            ExpectColumnValuesToBeUnique(column="cliente_id"),
            ExpectColumnValuesToNotBeNull(column="nome"),
        ],
    )


def test_ge_produtos():
    _run_suite(
        _load("landing_varejo", "produtos"),
        "produtos",
        [
            ExpectTableRowCountToBeGreaterThan(value=0),
            ExpectColumnValuesToNotBeNull(column="produto_id"),
            ExpectColumnValuesToBeUnique(column="produto_id"),
            ExpectColumnValuesToBeBetween(column="preco_sugerido", min_value=0),
        ],
    )


def test_ge_vendas():
    _run_suite(
        _load("landing_varejo", "vendas"),
        "vendas",
        [
            ExpectTableRowCountToBeGreaterThan(value=0),
            ExpectColumnValuesToNotBeNull(column="venda_id"),
            ExpectColumnValuesToNotBeNull(column="cliente_id"),
            ExpectColumnValuesToNotBeNull(column="produto_id"),
        ],
    )


def test_ge_usuarios():
    _run_suite(
        _load("landing_biblioteca", "usuarios"),
        "usuarios",
        [
            ExpectTableRowCountToBeGreaterThan(value=0),
            ExpectColumnValuesToNotBeNull(column="usuario_id"),
            ExpectColumnValuesToBeUnique(column="usuario_id"),
        ],
    )


def test_ge_emprestimos():
    _run_suite(
        _load("landing_biblioteca", "emprestimos"),
        "emprestimos",
        [
            ExpectTableRowCountToBeGreaterThan(value=0),
            ExpectColumnValuesToNotBeNull(column="emprestimo_id"),
            ExpectColumnValuesToNotBeNull(column="usuario_id"),
            ExpectColumnValuesToNotBeNull(column="livro_id"),
        ],
    )


def test_ge_pessoas():
    _run_suite(
        _load("landing_rede_social", "pessoas"),
        "pessoas",
        [
            ExpectTableRowCountToBeGreaterThan(value=0),
            ExpectColumnValuesToNotBeNull(column="pessoa_id"),
            ExpectColumnValuesToBeUnique(column="pessoa_id"),
        ],
    )
