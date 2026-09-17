#!/bin/bash
# Reset database to clean state — drops all 3 domain schemas + analytics
set -euo pipefail

export PGPASSWORD="${PGPASSWORD:-dbt}"
HOST="${HOST:-localhost}"
PORT="${PORT:-5437}"
USER="${USER:-dbt}"
DB="${DB:-portifolio}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "Resetting database ${DB}..."

psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" <<'SQL'
DROP SCHEMA IF EXISTS varejo      CASCADE;
DROP SCHEMA IF EXISTS biblioteca  CASCADE;
DROP SCHEMA IF EXISTS rede_social CASCADE;
DROP SCHEMA IF EXISTS analytics   CASCADE;
DROP SCHEMA IF EXISTS staging_varejo        CASCADE;
DROP SCHEMA IF EXISTS staging_biblioteca    CASCADE;
DROP SCHEMA IF EXISTS staging_rede_social   CASCADE;
DROP SCHEMA IF EXISTS intermediate_varejo   CASCADE;
DROP SCHEMA IF EXISTS intermediate_biblioteca  CASCADE;
DROP SCHEMA IF EXISTS intermediate_rede_social CASCADE;
DROP SCHEMA IF EXISTS analytics_varejo      CASCADE;
DROP SCHEMA IF EXISTS analytics_biblioteca  CASCADE;
DROP SCHEMA IF EXISTS analytics_rede_social CASCADE;
SQL

echo "Re-seeding OLTP..."
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -f oltp/init.sql

echo "  Done. Run 'make dbt-seed dbt-build' to rebuild analytics."

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
