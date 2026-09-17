#!/bin/bash
# run_all.sh — Pipeline completo: banco + dbt + API
set -e

export PGPASSWORD=dbt
DBT_DIR="ecommerce"

echo "================================================================"
echo "  DEH Portifólio — Pipeline Completo"
echo "================================================================"
echo ""

# 1. Infraestrutura
echo "→ Subindo containers..."
docker compose up -d postgres
echo "  Aguardando PostgreSQL..."
until docker compose exec postgres pg_isready -U dbt -d portifolio > /dev/null 2>&1; do
    sleep 2
done
echo "  ✓ PostgreSQL pronto"

# 2. dbt
echo ""
echo "→ Executando dbt seed..."
cd $DBT_DIR && uv run dbt seed --profiles-dir ~/.dbt --quiet
echo "  ✓ Seeds carregadas (estados_brasil)"

echo ""
echo "→ Construindo modelos dbt..."
echo "  [varejo] staging → intermediate → mart"
uv run dbt build --select tag:varejo --profiles-dir ~/.dbt --quiet
echo "  ✓ Varejo"

echo "  [biblioteca] staging → intermediate → mart"
uv run dbt build --select tag:biblioteca --profiles-dir ~/.dbt --quiet
echo "  ✓ Biblioteca"

echo "  [rede_social] staging → intermediate → mart"
uv run dbt build --select tag:rede_social --profiles-dir ~/.dbt --quiet
echo "  ✓ Rede Social"

echo ""
echo "→ Executando snapshots SCD Tipo 2..."
uv run dbt snapshot --profiles-dir ~/.dbt --quiet
echo "  ✓ Snapshots"

cd ..

# 3. API
echo ""
echo "→ Iniciando API..."
docker compose up -d api
echo "  ✓ API disponível em http://localhost:8000"
echo "  ✓ Documentação: http://localhost:8000/docs"
echo "  ✓ MCP endpoint: http://localhost:8000/mcp"

echo ""
echo "================================================================"
echo "  ✓ Pipeline completo!"
echo ""
echo "  Endpoints REST:"
echo "    GET /api/v1/varejo/dashboard"
echo "    GET /api/v1/biblioteca/dashboard"
echo "    GET /api/v1/rede_social/dashboard"
echo "    GET /api/v1/rede_social/recomendacoes/{pessoa_id}"
echo "================================================================"
