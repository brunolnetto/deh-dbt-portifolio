#!/bin/bash
cd /home/pingu/github/deh-dbt-essentials
source .venv/bin/activate
cd ecommerce

echo "🔄 Starting dbt build with corrected schema configuration..."
echo ""

dbt build --profiles-dir ~/.dbt

echo ""
echo "✓ Build complete!"
