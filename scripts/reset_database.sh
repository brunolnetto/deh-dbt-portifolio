#!/bin/bash
# Reset database to clean state
set -euo pipefail

export PGPASSWORD="${PGPASSWORD:-dbt}"
HOST="${HOST:-localhost}"
PORT="${PORT:-5435}"
USER="${USER:-dbt}"
DB="${DB:-shop}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "🔄 Resetting database..."

# Drop OLTP tables if they exist
echo "Dropping OLTP tables..."
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "DROP TABLE IF EXISTS shop.order_items CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "DROP TABLE IF EXISTS shop.products CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "DROP TABLE IF EXISTS shop.salespeople CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "DROP TABLE IF EXISTS shop.orders CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "DROP TABLE IF EXISTS shop.customers CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true

# Drop dbt-generated tables/views in shop and analytics
echo "Dropping dbt artifacts..."
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "DROP SCHEMA IF EXISTS analytics CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "DROP SCHEMA IF EXISTS shop CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true

# Create fresh schemas
echo "Creating schemas..."
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "CREATE SCHEMA IF NOT EXISTS shop;" 2>&1 | grep -E 'CREATE|ERROR' || true
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "CREATE SCHEMA IF NOT EXISTS analytics;" 2>&1 | grep -E 'CREATE|ERROR' || true

# Recreate OLTP tables
echo "Loading OLTP schema..."
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" < "$ROOT_DIR/oltp/init.sql" 2>&1 | tail -3

echo ""
echo "✓ Database reset complete"
echo ""
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" <<SQL
SELECT 'shop' as schema_name, COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'shop'
UNION ALL
SELECT 'analytics' as schema_name, COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'analytics'
ORDER BY schema_name;
SQL

echo ""
echo "Table counts:"
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "SELECT 'customers' as table_name, COUNT(*) as count FROM shop.customers UNION ALL SELECT 'orders', COUNT(*) FROM shop.orders UNION ALL SELECT 'salespeople', COUNT(*) FROM shop.salespeople UNION ALL SELECT 'products', COUNT(*) FROM shop.products UNION ALL SELECT 'order_items', COUNT(*) FROM shop.order_items;"
