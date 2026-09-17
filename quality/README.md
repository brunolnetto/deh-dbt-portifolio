# Quality Gates: pytest + Great Expectations + SODA

The portfolio analytics system enforces three layers of data quality validation on the landing tables (populated by the dlt extractor).

## Overview

| Layer | Tool | Scope | Triggers |
|-------|------|-------|----------|
| **Fast** | pytest | 13 landing tables: row count, PK not null | `make quality-local` or CI after dbt build |
| **Structural** | Great Expectations v1 | Per-domain column expectations (unique, range, type) | CI after dbt build |
| **Declarative** | SODA Core | YAML-based checks per domain (null, duplicate, value tests) | CI after dbt build or `make quality-check` |

---

## 1. pytest — Fast Validation

**File**: `quality/tests/test_pipeline.py`

Parametrized tests that verify all 13 landing tables have data and no NULL primary keys.

```python
@pytest.mark.parametrize("schema,table,pk", _TABLES)
def test_landing_not_empty(pg_conn, schema: str, table: str, pk: str):
    assert count > 0, f"{schema}.{table} is empty"

def test_landing_pk_not_null(pg_conn, schema: str, table: str, pk: str):
    assert nulls == 0, f"{schema}.{table}.{pk} has NULL values"
```

**Coverage**: varejo (clientes, produtos, vendas) + biblioteca (usuarios, livros, emprestimos, autores, multas) + rede_social (pessoas, leituras, conexoes, generos, livros)

### Run Locally
```bash
cd quality
pip install -e . -q
python -m pytest tests/test_pipeline.py -v
```

---

## 2. Great Expectations — Column-Level Validation

**File**: `quality/tests/test_ge_landing.py`

Defines column-level expectations per domain using GE v1 Pandas-based API:
- `ExpectColumnValuesToNotBeNull` (clientes.cliente_id, etc.)
- `ExpectColumnValuesToBeUnique` (primary keys)
- `ExpectColumnValuesToBeBetween` (numeric ranges: preco_sugerido ≥ 0)
- `ExpectTableRowCountToBeGreaterThan` (table not empty)

```python
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
```

**Coverage**: clientes, produtos, vendas, usuarios, emprestimos, pessoas

### Run Locally
```bash
cd quality
pip install -e . -q
python -m pytest tests/test_ge_landing.py -v
```

---

## 3. SODA Core — Declarative YAML Checks

**Config**: `quality/soda/configuration.yml`  
**Checks**: `quality/soda/checks/{varejo,biblioteca,rede_social}.yml`

SODA scans run declarative checks against landing tables:

```yaml
checks for landing_varejo.clientes:
  - row_count > 0:
      name: clientes must not be empty
  - missing_count(cliente_id) = 0:
      name: cliente_id must not be null
  - duplicate_count(cliente_id) = 0:
      name: cliente_id must be unique
  - invalid_count(preco_sugerido) = 0:
      valid min: 0
      name: preco_sugerido must be non-negative
```

**Coverage**: All 13 landing tables across 3 domains with domain-specific business rules.

### Run Locally
```bash
cd quality
pip install -e . -q
python -m pytest tests/test_soda_landing.py -v
```

---

## Running Quality Gates

### Local Development

```bash
# Fast checks only (pytest)
make quality-local

# Or run each layer independently:
cd quality && pip install -e . -q
python -m pytest tests/test_pipeline.py tests/test_ge_landing.py tests/test_soda_landing.py -v
```

### Docker (isolated environment)

```bash
# Run quality service standalone
docker compose --profile quality up --build quality

# Or shell into quality environment
make quality-shell
```

### CI/CD (GitHub Actions)

Quality gates automatically run after dbt build succeeds:
1. `test_pipeline.py` — pytest landing table counts
2. `test_ge_landing.py` — Great Expectations column expectations
3. `test_soda_landing.py` — SODA declarative checks

**Failure behavior**: If any quality check fails, the workflow stops and the PR/commit is blocked.

---

## Quality Gate Flow

```
┌─ dbt build (landing tables populated)
│
├─ pytest (fast row-count + PK null checks)
│  └─ 13 tables × 2 assertions = 26 tests
│
├─ Great Expectations (column expectations)
│  └─ 6 test suites (clientes, produtos, vendas, usuarios, emprestimos, pessoas)
│
└─ SODA Core (declarative checks)
   └─ 3 domain files × ~10 checks each = ~30 checks
```

If all pass → ✅ Landing layer is valid for downstream dbt transforms.

---

## Adding New Quality Checks

### Add pytest check
Edit `quality/tests/test_pipeline.py` and add to `_TABLES` parametrize list.

### Add Great Expectations check
Edit `quality/tests/test_ge_landing.py` and add a new `test_ge_*()` function with expectation suite.

### Add SODA check
Edit `quality/soda/checks/{domain}.yml` and add a new check block (no code, just YAML).

---

## Dependencies

- **pytest**: Parametrized test framework
- **great-expectations**: Column-level validation expectations
- **soda-core-postgres**: Declarative SQL-based quality scans
- **psycopg**: PostgreSQL connection pool
- **pandas**: In-memory data frame for GE

See `quality/pyproject.toml` for versions.
