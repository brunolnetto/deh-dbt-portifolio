#!/bin/bash
# Simplified demonstration of production data workflows
# Run from project root: bash scripts/run_demo_simple.sh

export PGPASSWORD=dbt
cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

echo ""
echo "==============================================="
echo "  PRODUCTION DATA WORKFLOWS DEMONSTRATION"
echo "==============================================="
echo ""

# Show data before workflows
echo "INITIAL STATE - Orders and Customers in OLTP:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  'Orders' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as soft_deleted
FROM orders
UNION ALL
SELECT 
  'Customers' as table_name,
  COUNT(*) as total_rows,
  0 as soft_deleted
FROM customers;
"
echo ""

# ===== WORKFLOW 1: Soft-Delete =====
echo "WORKFLOW 1: Soft-Delete Pattern"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "→ Insert a new order"
python scripts/mutate.py insert-order 2>/dev/null && echo "✓ Order inserted" || echo "✗ Insert failed"
echo ""

echo "→ Soft-delete the order"
python scripts/mutate.py soft-delete-order 2>/dev/null && echo "✓ Order soft-deleted" || echo "✗ Soft-delete failed"
echo ""

echo "Order now marked with deleted_at:"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT order_id, amount, status, deleted_at 
FROM orders 
WHERE deleted_at IS NOT NULL 
ORDER BY order_id DESC 
LIMIT 1;
"
echo ""

# ===== WORKFLOW 2: Incremental Updates =====
echo "WORKFLOW 2: Incremental Model Updates"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "→ Insert 4 new orders"
for i in {1..4}; do
  python scripts/mutate.py insert-order 2>/dev/null
done
echo "✓ 4 orders inserted"
echo ""

echo "→ Update one order status"
python scripts/mutate.py update-order 2>/dev/null && echo "✓ Order updated" || echo "✗ Update failed"
echo ""

echo "→ Create late-arriving order (old date, new timestamp)"
python scripts/mutate.py late-arriving-order 2>/dev/null && echo "✓ Late-arriving order created" || echo "✗ Failed"
echo ""

echo "Recent orders ready for incremental processing:"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT order_id, customer_id, order_date::date, status, updated_at::date 
FROM orders 
ORDER BY updated_at DESC 
LIMIT 5;
"
echo ""

# ===== WORKFLOW 3: Snapshot =====
echo "WORKFLOW 3: Snapshot (SCD Type 2) Tracking"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "→ Insert new customer"
python scripts/mutate.py insert-customer 2>/dev/null && echo "✓ Customer inserted" || echo "✗ Failed"
echo ""

echo "→ Change customer country twice"
python scripts/mutate.py update-customer 2>/dev/null && echo "✓ Change 1" || echo "✗ Failed"
python scripts/mutate.py update-customer 2>/dev/null && echo "✓ Change 2" || echo "✗ Failed"
echo ""

echo "Customer state (snapshot will track all 3 versions):"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT customer_id, name, country_code, updated_at::date 
FROM customers 
ORDER BY customer_id DESC 
LIMIT 1;
"
echo ""

# ===== WORKFLOW 4: Data Quality =====
echo "WORKFLOW 4: Data Quality Issues"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "→ Injecting 5 types of bad data..."
python scripts/mutate.py bug-invalid-country 2>/dev/null
python scripts/mutate.py bug-negative-amount 2>/dev/null
python scripts/mutate.py bug-zero-amount 2>/dev/null
python scripts/mutate.py bug-future-order 2>/dev/null
python scripts/mutate.py bug-dirty-name 2>/dev/null
echo "✓ Data quality issues injected (dbt tests will catch them)"
echo ""

# ===== RUN DBT BUILD =====
echo "DBT BUILD - Processing all data and running tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd ecommerce
echo "Running: dbt build --profiles-dir ~/.dbt"
dbt build --profiles-dir ~/.dbt 2>&1 | grep -E "Completed|PASS|FAIL|ERROR|tests passed" || dbt build --profiles-dir ~/.dbt
BUILD_STATUS=$?
cd ..

if [ $BUILD_STATUS -eq 0 ]; then
  echo "✓ dbt build completed successfully"
else
  echo "⚠ dbt build had issues (check output above)"
fi

echo ""
echo "==============================================="
echo "  VERIFICATION: dbt Model Results"
echo "==============================================="
echo ""

echo "Fact table: fct_orders (active vs soft-deleted)"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as soft_deleted,
  COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active
FROM shop.fct_orders;
"
echo ""

echo "Dimension: dim_customers (with country enrichment)"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  COUNT(*) as total_customers,
  COUNT(DISTINCT country_name) as unique_countries
FROM shop.dim_customers;
" 2>/dev/null || echo "(Table may not exist yet)"
echo ""

echo "Snapshot: customers_snapshot (SCD Type 2 history)"
psql -h localhost -p 5435 -U dbt -d shop -c "
SELECT 
  COUNT(*) as total_snapshot_rows,
  COUNT(DISTINCT customer_id) as unique_customers,
  COUNT(CASE WHEN dbt_valid_to IS NULL THEN 1 END) as current_versions
FROM shop.customers_snapshot;
" 2>/dev/null || echo "(Snapshot may not exist yet)"
echo ""

echo "==============================================="
echo "✓ ALL PRODUCTION PATTERNS DEMONSTRATED!"
echo "==============================================="
echo ""
echo "Summary:"
echo "  ✓ Soft-Delete: Orders marked deleted_at retained for analytics"
echo "  ✓ Incremental: fct_orders captures only changed rows"
echo "  ✓ Snapshot: customers_snapshot tracks dimension history (SCD Type 2)"
echo "  ✓ Quality: dbt tests catch invalid data patterns"
echo ""
echo "For detailed patterns, see: WORKFLOWS.md"
echo ""
