"""Great Expectations validation for landing tables using the GE v1 Pandas-based API."""
import os
from typing import Any

import great_expectations as gx
import pandas as pd
import psycopg
import pytest

from conftest import POSTGRES_DSN


def _load(schema: str, table: str) -> pd.DataFrame:
    with psycopg.connect(POSTGRES_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {schema}.{table}")
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]
    return pd.DataFrame(rows, columns=cols)


def _run_suite(df: pd.DataFrame, name: str, expectations: list[dict]) -> None:
    """
    Run a GE v1 ExpectationSuite on a DataFrame.
    
    Args:
        df: DataFrame to validate
        name: Suite name (used for context)
        expectations: List of expectation dicts with 'type' and 'kwargs' keys
            e.g., [
                {'type': 'expect_table_row_count_to_be_between', 'kwargs': {'min_value': 1}},
                {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'cliente_id'}},
            ]
    """
    ctx = gx.get_context()
    ds = ctx.data_sources.add_pandas(name=f"ds_{name}")
    asset = ds.add_dataframe_asset(name=name)
    batch_def = asset.add_batch_definition_whole_dataframe("batch")
    
    suite = ctx.suites.add(gx.ExpectationSuite(name=name))
    for exp in expectations:
        exp_type = exp['type']
        exp_kwargs = exp.get('kwargs', {})
        suite.add_expectation(gx.Expectation(type=exp_type, kwargs=exp_kwargs))
    
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
            {'type': 'expect_table_row_count_to_be_between', 'kwargs': {'min_value': 1}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'cliente_id'}},
            {'type': 'expect_column_values_to_be_unique', 'kwargs': {'column': 'cliente_id'}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'nome'}},
        ],
    )


def test_ge_produtos():
    _run_suite(
        _load("landing_varejo", "produtos"),
        "produtos",
        [
            {'type': 'expect_table_row_count_to_be_between', 'kwargs': {'min_value': 1}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'produto_id'}},
            {'type': 'expect_column_values_to_be_unique', 'kwargs': {'column': 'produto_id'}},
            {'type': 'expect_column_values_to_be_between', 'kwargs': {'column': 'preco_sugerido', 'min_value': 0}},
        ],
    )


def test_ge_vendas():
    _run_suite(
        _load("landing_varejo", "vendas"),
        "vendas",
        [
            {'type': 'expect_table_row_count_to_be_between', 'kwargs': {'min_value': 1}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'venda_id'}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'cliente_id'}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'produto_id'}},
        ],
    )


def test_ge_usuarios():
    _run_suite(
        _load("landing_biblioteca", "usuarios"),
        "usuarios",
        [
            {'type': 'expect_table_row_count_to_be_between', 'kwargs': {'min_value': 1}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'usuario_id'}},
            {'type': 'expect_column_values_to_be_unique', 'kwargs': {'column': 'usuario_id'}},
        ],
    )


def test_ge_emprestimos():
    _run_suite(
        _load("landing_biblioteca", "emprestimos"),
        "emprestimos",
        [
            {'type': 'expect_table_row_count_to_be_between', 'kwargs': {'min_value': 1}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'emprestimo_id'}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'usuario_id'}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'livro_id'}},
        ],
    )


def test_ge_pessoas():
    _run_suite(
        _load("landing_rede_social", "pessoas"),
        "pessoas",
        [
            {'type': 'expect_table_row_count_to_be_between', 'kwargs': {'min_value': 1}},
            {'type': 'expect_column_values_to_not_be_null', 'kwargs': {'column': 'pessoa_id'}},
            {'type': 'expect_column_values_to_be_unique', 'kwargs': {'column': 'pessoa_id'}},
        ],
    )
