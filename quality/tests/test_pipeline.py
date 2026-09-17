"""Basic pytest checks on landing tables — fast row-count and null assertions."""
import pytest

_TABLES: list[tuple[str, str, str]] = [
    # (schema, table, pk_column)
    ("landing_varejo", "clientes", "cliente_id"),
    ("landing_varejo", "produtos", "produto_id"),
    ("landing_varejo", "vendas", "venda_id"),
    ("landing_biblioteca", "usuarios", "usuario_id"),
    ("landing_biblioteca", "livros", "livro_id"),
    ("landing_biblioteca", "emprestimos", "emprestimo_id"),
    ("landing_biblioteca", "autores", "autor_id"),
    ("landing_biblioteca", "multas", "emprestimo_id"),
    ("landing_rede_social", "pessoas", "pessoa_id"),
    ("landing_rede_social", "leituras", "leitura_id"),
    ("landing_rede_social", "conexoes", "conexao_id"),
    ("landing_rede_social", "generos", "genero_id"),
    ("landing_rede_social", "livros", "livro_id"),
]


@pytest.mark.parametrize("schema,table,pk", _TABLES)
def test_landing_not_empty(pg_conn, schema: str, table: str, pk: str):
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        count = cur.fetchone()[0]
    assert count > 0, f"{schema}.{table} is empty — extractor may not have run yet"


@pytest.mark.parametrize("schema,table,pk", _TABLES)
def test_landing_pk_not_null(pg_conn, schema: str, table: str, pk: str):
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table} WHERE {pk} IS NULL")
        nulls = cur.fetchone()[0]
    assert nulls == 0, f"{schema}.{table}.{pk} has {nulls} NULL values"
