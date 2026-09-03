#!/bin/bash
# Demonstration of production data workflows

export PGPASSWORD=dbt
cd "$(dirname "$0")/.."

echo ""
echo "==============================================="
echo "  PRODUCTION DATA WORKFLOWS DEMONSTRATION"
echo "==============================================="
echo ""

# ===== WORKFLOW 1: Soft-Delete =====

echo "WORKFLOW 1: Soft-Delete Pattern"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Step 1: Insert a new order"
python3 scripts/mutate.py insert-order
echo ""

echo "Step 2: View order in OLTP (before soft-delete)"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT order_id, customer_id, amount, status, deleted_at 
FROM orders 
WHERE order_id = (SELECT max(order_id) FROM orders) 
LIMIT 1;
SQL
echo ""

echo "Step 3: Soft-delete the order"
python3 scripts/mutate.py soft-delete-order
echo ""

echo "Step 4: View order after soft-delete (still in table, marked)"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT order_id, amount, status, deleted_at, updated_at 
FROM orders 
WHERE deleted_at IS NOT NULL 
ORDER BY order_id DESC 
LIMIT 1;
SQL
echo ""

echo "✓ Soft-delete workflow: Order marked as deleted but retained for analytics"
echo ""

# ===== WORKFLOW 2: Incremental Updates =====

echo "WORKFLOW 2: Incremental Model Updates"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Step 1: Insert 4 new orders (incremental will capture via updated_at)"
python3 scripts/mutate.py insert-order
python3 scripts/mutate.py insert-order
python3 scripts/mutate.py insert-order
python3 scripts/mutate.py insert-order
echo ""

echo "Step 2: Update an order status (incremental will see updated_at change)"
python3 scripts/mutate.py update-order
echo ""

echo "Step 3: Create late-arriving order (old order_date, current updated_at)"
python3 scripts/mutate.py late-arriving-order
echo ""

echo "Recent orders that will trigger incremental:"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT order_id, customer_id, order_date, status, updated_at 
FROM orders 
ORDER BY updated_at DESC 
LIMIT 6;
SQL
echo ""

echo "✓ Incremental model events: 5 new rows + 1 update + 1 late-arrival"
echo ""

# ===== WORKFLOW 3: Snapshot =====

echo "WORKFLOW 3: Snapshot (SCD Type 2) Tracking"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Step 1: Insert a new customer"
python3 scripts/mutate.py insert-customer
echo ""

echo "Step 2: Update customer country (change 1)"
python3 scripts/mutate.py update-customer
echo ""

echo "Step 3: Update customer country (change 2)"
python3 scripts/mutate.py update-customer
echo ""

echo "Customer change history in OLTP (most recent):"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT customer_id, name, country_code, updated_at 
FROM customers 
ORDER BY customer_id DESC 
LIMIT 1;
SQL
echo ""

echo "✓ Snapshot will track: Version 1 → Version 2 → Version 3 (current)"
echo ""

# ===== WORKFLOW 4: Data Quality =====

echo "WORKFLOW 4: Data Quality Issues (for dbt test detection)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Injecting data quality issues..."
python3 scripts/mutate.py bug-invalid-country
python3 scripts/mutate.py bug-negative-amount
python3 scripts/mutate.py bug-zero-amount
python3 scripts/mutate.py bug-future-order
python3 scripts/mutate.py bug-dirty-name
echo ""

echo "Invalid data in OLTP (will be caught by dbt tests):"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT order_id, amount FROM orders WHERE amount <= 0 LIMIT 3;
SQL
echo ""

echo "✓ Data quality issues injected - dbt tests will catch them"
echo ""

# ===== RUN DBT BUILD =====

echo "DBT BUILD - Capture all changes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Executing: cd ecommerce && dbt build --profiles-dir ~/.dbt"
echo ""
cd ecommerce
dbt build --profiles-dir ~/.dbt 2>&1 | tail -40
cd ..

echo ""
echo "==============================================="
echo "  VERIFICATION: dbt Model Results"
echo "==============================================="
echo ""

echo "Fact table: fct_orders (active vs soft-deleted)"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT 
  COUNT(*) as total_rows,
  COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as soft_deleted,
  COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active
FROM fct_orders;
SQL
echo ""

echo "Dimension: dim_customers (with enrichment)"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT 
  COUNT(*) as total_customers,
  COUNT(DISTINCT country_name) as unique_countries
FROM dim_customers;
SQL
echo ""

echo "Snapshot: customers_snapshot (SCD Type 2 history)"
psql -h localhost -p 5435 -U dbt -d shop << SQL
SELECT 
  COUNT(*) as total_snapshot_rows,
  COUNT(DISTINCT customer_id) as unique_customers,
  COUNT(CASE WHEN dbt_valid_to IS NULL THEN 1 END) as current_versions
FROM customers_snapshot;
SQL
echo ""

echo "==============================================="
echo "✓ ALL PRODUCTION PATTERNS DEMONSTRATED!"
echo "==============================================="
echo ""
echo "Summary:"
echo "  ✓ Soft-Delete: Orders marked deleted_at retained for analytics"
echo "  ✓ Incremental: fct_orders captures only changed rows (efficient)"
echo "  ✓ Snapshot: customers_snapshot tracks dimension history (SCD Type 2)"
echo "  ✓ Quality: dbt tests catch invalid data patterns"
echo ""
