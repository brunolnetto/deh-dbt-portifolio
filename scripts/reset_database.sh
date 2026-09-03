#!/bin/bash
# Reset database to clean state

export PGPASSWORD=dbt
HOST=localhost
PORT=5435
USER=dbt
DB=shop

echo "🔄 Resetting database..."

# Drop OLTP tables if they exist
echo "Dropping OLTP tables..."
psql -h $HOST -p $PORT -U $USER -d $DB -c "DROP TABLE IF EXISTS shop.orders CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true
psql -h $HOST -p $PORT -U $USER -d $DB -c "DROP TABLE IF EXISTS shop.customers CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true

# Drop dbt-generated tables/views in shop and analytics
echo "Dropping dbt artifacts..."
psql -h $HOST -p $PORT -U $USER -d $DB -c "DROP SCHEMA IF EXISTS shop_analytics CASCADE;" 2>&1 | grep -E 'DROP|ERROR' || true

# Create fresh schemas
echo "Creating schemas..."
psql -h $HOST -p $PORT -U $USER -d $DB -c "CREATE SCHEMA IF NOT EXISTS shop;" 2>&1 | grep -E 'CREATE|ERROR' || true
psql -h $HOST -p $PORT -U $USER -d $DB -c "CREATE SCHEMA IF NOT EXISTS analytics;" 2>&1 | grep -E 'CREATE|ERROR' || true

# Recreate OLTP tables
echo "Loading OLTP schema..."
cd /home/pingu/github/deh-dbt-essentials
psql -h $HOST -p $PORT -U $USER -d $DB < oltp/init.sql 2>&1 | tail -3

# Verify
echo ""
echo "✓ Database reset complete"
echo ""
psql -h $HOST -p $PORT -U $USER -d $DB << SQL
SELECT 'shop' as schema, COUNT(*) as tables 
FROM information_schema.tables 
WHERE table_schema = 'shop'
UNION ALL
SELECT 'analytics' as schema, COUNT(*) 
FROM information_schema.tables 
WHERE table_schema = 'analytics'
ORDER BY schema;
SQL

echo ""
echo "Table counts:"
psql -h $HOST -p $PORT -U $USER -d $DB -c "SELECT 'customers' as table_name, COUNT(*) as count FROM shop.customers UNION ALL SELECT 'orders', COUNT(*) FROM shop.orders;"
