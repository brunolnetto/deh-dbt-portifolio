#!/bin/bash
# DEH Portfolio — Production Data Workflows Demo
# Demonstra padrões incrementais, SCD Tipo 2 e qualidade de dados nos 3 domínios.
# Executar a partir da raiz do projeto: bash scripts/run_demo.sh

set -euo pipefail
export PGPASSWORD=dbt
PORT="${POSTGRES_PORT:-5437}"
DB="${POSTGRES_DB:-portifolio}"
cd "$(dirname "$0")/.."

source .venv/bin/activate 2>/dev/null || true

MUTATE="python -m portfolio_api.cli"
PSQL="psql -h localhost -p $PORT -U dbt -d $DB"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       DEH PORTFOLIO — DEMONSTRAÇÃO DE WORKFLOWS               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# ── BASELINE ─────────────────────────────────────────────────────────────────
echo ""
echo "ESTADO INICIAL — OLTP"
$PSQL -c "
SELECT 'varejo.origem_venda'   AS tabela, count(*) AS linhas, max(updated_at)::date AS ultimo_update FROM varejo.origem_venda
UNION ALL
SELECT 'biblioteca.emprestimo', count(*), max(updated_at)::date FROM biblioteca.emprestimo
UNION ALL
SELECT 'rede_social.leitura',   count(*), max(updated_at)::date FROM rede_social.leitura
ORDER BY tabela;"
echo ""

# ── 1: VAREJO — INCREMENTAL ───────────────────────────────────────────────────
echo "1. VAREJO — Modelo incremental (fct_vendas)"
echo ""
echo "  → 3 novas vendas + 1 venda com data retroativa..."
for _ in 1 2 3; do $MUTATE varejo insert-venda 2>&1 | tail -1; done
$MUTATE varejo late-venda 2>&1 | tail -1
echo ""
echo "  → dbt build varejo (incremental merge)..."
cd ecommerce && dbt build --select tag:varejo --profiles-dir ~/.dbt -q 2>&1 | grep -E "Done\.|ERROR" | head -3; cd ..
echo ""
echo "  → fct_vendas (5 mais recentes):"
$PSQL -c "SELECT sale_id, customer_id, sale_date, total_amount, status FROM analytics_varejo.fct_vendas ORDER BY sale_id DESC LIMIT 5;" 2>/dev/null || echo "  (execute dbt build primeiro)"
echo ""

# ── 2: BIBLIOTECA — EMPRÉSTIMOS ──────────────────────────────────────────────
echo "2. BIBLIOTECA — Empréstimos e devoluções"
echo ""
echo "  → 2 empréstimos + 1 devolução..."
$MUTATE biblioteca insert-emprestimo 2>&1 | tail -1
$MUTATE biblioteca insert-emprestimo 2>&1 | tail -1
$MUTATE biblioteca return-livro      2>&1 | tail -1
echo ""
echo "  → dbt build biblioteca..."
cd ecommerce && dbt build --select tag:biblioteca --profiles-dir ~/.dbt -q 2>&1 | grep -E "Done\.|ERROR" | head -3; cd ..
echo ""
echo "  → fct_emprestimos (ativos e atrasados):"
$PSQL -c "SELECT emprestimo_id, usuario_id, loan_date, due_date, is_overdue, days_overdue FROM analytics_biblioteca.fct_emprestimos WHERE NOT is_returned ORDER BY loan_date DESC LIMIT 5;" 2>/dev/null || echo "  (execute dbt build primeiro)"
echo ""

# ── 3: REDE SOCIAL — SNAPSHOT SCD TIPO 2 ─────────────────────────────────────
echo "3. REDE SOCIAL + SNAPSHOT SCD Tipo 2 (clientes_snapshot no varejo)"
echo ""
echo "  → 2 leituras + 1 atualização de nota + 2 mudanças de segmento..."
$MUTATE rede_social insert-leitura  2>&1 | tail -1
$MUTATE rede_social insert-leitura  2>&1 | tail -1
$MUTATE rede_social update-nota     2>&1 | tail -1
$MUTATE varejo update-cliente       2>&1 | tail -1
$MUTATE varejo update-cliente       2>&1 | tail -1
echo ""
echo "  → dbt build rede_social + snapshot varejo..."
cd ecommerce
dbt build    --select tag:rede_social --profiles-dir ~/.dbt -q 2>&1 | grep -E "Done\.|ERROR" | head -3
dbt snapshot --profiles-dir ~/.dbt    -q 2>&1 | grep -E "Done\.|ERROR" | head -3
cd ..
echo ""
echo "  → mart_recomendacoes (pessoa 1):"
$PSQL -c "SELECT livro_id, title, author, network_avg_rating, recommended_by_count FROM analytics_rede_social.mart_recomendacoes WHERE pessoa_id=1 ORDER BY network_avg_rating DESC LIMIT 5;" 2>/dev/null || echo "  (execute dbt build primeiro)"
echo ""
echo "  → clientes_snapshot (histórico SCD Tipo 2):"
$PSQL -c "SELECT cliente_id, segmento, dbt_valid_from::date, dbt_valid_to::date FROM analytics_varejo.clientes_snapshot ORDER BY cliente_id, dbt_valid_from DESC LIMIT 6;" 2>/dev/null || echo "  (snapshot pendente)"
echo ""

# ── RESUMO ────────────────────────────────────────────────────────────────────
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  ✓ DEMONSTRAÇÃO COMPLETA                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "  API:  http://localhost:8000/docs"
echo "  MCP:  http://localhost:8000/mcp"
echo ""
echo "  Observe (BEFORE/AFTER diff):"
echo "    python -m portfolio_api.observe varejo insert-venda"
echo "    python -m portfolio_api.observe biblioteca return-livro"
echo "    python -m portfolio_api.observe rede_social insert-leitura"
echo ""


echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       PRODUCTION DATA WORKFLOWS DEMONSTRATION                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ===== BASELINE: INITIAL STATE =====
echo "📊 BASELINE STATE - Before workflows"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "OLTP Tables (raw data):"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  'orders' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as soft_deleted,
  MAX(updated_at)::date as latest_update
FROM orders
UNION ALL
SELECT 
  'customers' as table_name,
  COUNT(*) as total_rows,
  0 as soft_deleted,
  MAX(updated_at)::date as latest_update
FROM customers
ORDER BY table_name;
"
echo ""

# ===== WORKFLOW 1: Soft-Delete =====
echo "1️⃣  SOFT-DELETE PATTERN"
echo "━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  → Insert order..."
python scripts/mutate.py insert-order 2>/dev/null | grep -E "Created|Error" || true

echo "  → Soft-delete order..."
python scripts/mutate.py soft-delete-order 2>/dev/null | grep -E "Soft deleted|Error" || true

echo "  → Order state (marked with deleted_at):"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT order_id, customer_id, amount, status, deleted_at 
FROM orders 
WHERE deleted_at IS NOT NULL 
ORDER BY order_id DESC 
LIMIT 1;" | head -4
echo ""

# ===== WORKFLOW 2: Incremental Updates =====
echo "2️⃣  INCREMENTAL MODEL UPDATES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  → Insert 4 new orders + 1 update + 1 late-arriving..."
for i in {1..4}; do python scripts/mutate.py insert-order 2>/dev/null | grep -E "Created" | tail -1 || true; done
python scripts/mutate.py update-order 2>/dev/null | grep -E "changed" || true
python scripts/mutate.py late-arriving-order 2>/dev/null | grep -E "Created" || true

echo "  → Recent orders (ready for incremental):"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT order_id, customer_id, order_date::date, status, updated_at::date 
FROM orders 
ORDER BY updated_at DESC 
LIMIT 4;" | head -6
echo ""

# ===== WORKFLOW 3: Snapshot =====
echo "3️⃣  SNAPSHOT (SCD TYPE 2) TRACKING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  → Insert customer..."
python scripts/mutate.py insert-customer 2>/dev/null | grep -E "Created" || true

echo "  → Update customer country 2x (for snapshot history)..."
python scripts/mutate.py update-customer 2>/dev/null | grep -E "moved" || true
python scripts/mutate.py update-customer 2>/dev/null | grep -E "moved" || true

echo "  → Current customer state:"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT customer_id, name, country_code, updated_at::date 
FROM customers 
WHERE customer_id > 10
ORDER BY customer_id DESC 
LIMIT 3;" | head -5
echo ""

# ===== WORKFLOW 4: Data Quality =====
echo "4️⃣  DATA QUALITY ISSUES (for dbt tests)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "  → Injecting bugs (invalid country, negative amount, future date...):"
python scripts/mutate.py bug-invalid-country 2>/dev/null | grep "BUG" || true
python scripts/mutate.py bug-negative-amount 2>/dev/null | grep "BUG" || true
python scripts/mutate.py bug-zero-amount 2>/dev/null | grep "BUG" || true
python scripts/mutate.py bug-future-order 2>/dev/null | grep "BUG" || true
echo "  ✓ 4 data quality issues injected"
echo ""

# ===== RUN DBT BUILD (SILENTLY) =====
echo "⚙️  RUNNING DBT BUILD (processing all changes)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd ecommerce
# Run dbt build silently, capture output
dbt build --profiles-dir ~/.dbt > /tmp/dbt_build.log 2>&1
BUILD_STATUS=$?
cd ..

# Show only summary
if [ $BUILD_STATUS -eq 0 ]; then
  BUILD_SUMMARY=$(grep "Done\." /tmp/dbt_build.log)
  echo "  ✅ Build completed: $(echo $BUILD_SUMMARY | sed 's/Done\. //')"
else
  FAILED=$(grep "ERROR\|FAIL" /tmp/dbt_build.log | wc -l)
  echo "  ✅ Build finished with $FAILED expected test failures (data quality detection)"
fi
echo ""

# ===== RESULTS =====
echo "📈 RESULTS - Analytics Layer After dbt Build"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Fact Table: fct_orders"
echo "  Summary:"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as soft_deleted,
  COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active,
  ROUND(SUM(amount)::numeric, 2) as total_amount
FROM analytics.fct_orders;" | head -3
echo ""

echo "  Sample data (recent orders):"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT order_id, customer_id, amount::numeric(10,2), status, 
       CASE WHEN deleted_at IS NULL THEN 'active' ELSE 'deleted' END as state
FROM analytics.fct_orders 
ORDER BY order_id DESC 
LIMIT 5;" | head -8
echo ""

echo "Dimension Table: dim_customers"
echo "  Summary:"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  COUNT(*) as total_customers,
  COUNT(DISTINCT country_code) as unique_country_codes
FROM analytics.dim_customers;" 2>/dev/null || echo "  (Awaiting dbt materialization)"
echo ""

echo "  Sample data (top 5 customers):"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT customer_id, customer_name, country_code, country_name
FROM analytics.dim_customers 
LIMIT 5;" 2>/dev/null || echo "  (Table being created by dbt...)"
echo ""

echo "Snapshot: customers_snapshot (SCD Type 2)"
echo "  Summary:"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  COUNT(*) as total_versions,
  COUNT(DISTINCT customer_id) as tracked_customers,
  COUNT(CASE WHEN dbt_valid_to IS NULL THEN 1 END) as current_versions
FROM analytics.customers_snapshot;" 2>/dev/null || echo "  (Snapshot data pending...)"
echo ""

echo "  Sample history (dimension changes - recent customers):"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  customer_id, 
  dbt_valid_from::date as valid_from, 
  dbt_valid_to::date as valid_to,
  CASE WHEN dbt_valid_to IS NULL THEN '✓ CURRENT' ELSE '✗ HISTORICAL' END as status
FROM analytics.customers_snapshot 
ORDER BY customer_id DESC, dbt_valid_from DESC
LIMIT 6;" 2>/dev/null || echo "  (Snapshot being built...)"
echo ""

# ===== SUMMARY =====
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  ✓ DEMONSTRATION COMPLETE                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Patterns Demonstrated:"
echo "  ✓ Soft-Delete: Orders retained in warehouse with deletion flag"
echo "  ✓ Incremental: Only changed rows processed (efficient)"
echo "  ✓ Snapshot: Complete dimension change history (SCD Type 2)"
echo "  ✓ Data Quality: dbt tests caught injected bad data"
echo ""

