#!/bin/bash
set -e

cd /home/pingu/github/deh-dbt-portifolio

echo "=== COMMIT 1: Infrastructure & CI/CD Refactoring ==="
git add .github/workflows/dbt-ci.yml app/Dockerfile app/pyproject.toml docker-compose.yml
git commit -m "refactor: update infrastructure for multi-domain portfolio

- Update .github/workflows/dbt-ci.yml: add domain-scoped builds for varejo, biblioteca, rede_social
- Update app/Dockerfile: switch to portfolio_api package
- Update app/pyproject.toml: consolidate dependencies for multi-domain support
- Update docker-compose.yml: configure postgres, api, and mutator services"

echo ""
echo "=== COMMIT 2: OLTP Database Schema & Configuration ==="
git add oltp/init.sql ecommerce/profiles.yml
git commit -m "feat: initialize OLTP schemas for 3 domains (varejo, biblioteca, rede_social)

- oltp/init.sql: Create domain-specific OLTP tables with proper constraints
  * varejo: origen_cliente, origin_produto, origin_venda
  * biblioteca: usuario, livro, emprestimo, multa, autor, livro_autor
  * rede_social: pessoa, livro, leitura, conexao_social, genero, pessoa_preferencia
- ecommerce/profiles.yml: dbt profile configuration for multi-domain project"

echo ""
echo "=== COMMIT 3: dbt Project Foundation ==="
git add ecommerce/dbt_project.yml ecommerce/macros/generate_schema_name.sql ecommerce/seeds/estados_brasil.csv
git commit -m "feat: establish dbt multi-domain architecture with schema routing

- ecommerce/dbt_project.yml: Configure portfolio project with domain tagging
- ecommerce/macros/generate_schema_name.sql: Implement multi-domain schema routing
- ecommerce/seeds/estados_brasil.csv: Add reference data for regional analysis"

echo ""
echo "=== COMMIT 4: Staging Models for All Domains ==="
git add ecommerce/models/staging/
git commit -m "feat: add staging layer models for 3 domains

- varejo (retail): stg_clientes, stg_produtos, stg_vendas
- biblioteca (library): stg_usuarios, stg_livros, stg_emprestimos, stg_autores
- rede_social (social): stg_pessoas, stg_leituras, stg_conexoes, stg_generos"

echo ""
echo "=== COMMIT 5: Intermediate Models for Data Enrichment ==="
git add ecommerce/models/intermediate/
git commit -m "feat: add intermediate layer models for data enrichment

- varejo: int_clientes_enriquecidos, int_vendas_por_cliente
- biblioteca: int_emprestimos_por_usuario, int_livros_com_autores
- rede_social: int_leituras_por_pessoa, int_livros_populares"

echo ""
echo "=== COMMIT 6: Mart Models for Analytics ==="
git add ecommerce/models/mart/ ecommerce/snapshots/customers_snapshot.yml
git commit -m "feat: add mart layer models and SCD Type 2 snapshot

Mart Models:
- varejo: dim_clientes, dim_produtos, fct_vendas (incremental), mart_clientes_vendas
- biblioteca: dim_livros, dim_usuarios, fct_emprestimos (incremental), mart_usuario_emprestimos
- rede_social: dim_pessoas, dim_livros_rede, fct_leituras, fct_conexoes, mart_recomendacoes

Snapshot:
- clientes_snapshot: SCD Type 2 tracking on varejo.origem_cliente (segmento changes)"

echo ""
echo "=== COMMIT 7: API Refactoring - From ecommerce_api to portfolio_api ==="
git add app/src/portfolio_api/ 
git rm -r app/src/ecommerce_api/
git commit -m "refactor: consolidate API to multi-domain portfolio_api package

Old Package Removed:
- app/src/ecommerce_api/ (single-domain retail-only API)

New Package Created:
- app/src/portfolio_api/main.py: FastAPI entry point with 3 domain routers
- app/src/portfolio_api/config.py: Environment-based settings
- app/src/portfolio_api/infrastructure/{varejo,biblioteca,rede_social}/repository.py: Async query interfaces
- app/src/portfolio_api/presentation/api/{varejo,biblioteca,rede_social}.py: REST endpoints (15+ routes)
- app/src/portfolio_api/presentation/mcp/tools.py: 8 MCP tools for Claude integration
- app/src/portfolio_api/mutator.py: Async OLTP mutation sidecar
- app/src/portfolio_api/cli.py: Manual mutation CLI interface
- app/src/portfolio_api/observe.py: BEFORE/AFTER observation tool with dbt integration
- app/src/portfolio_api/mcp_server.py: Standalone stdio MCP entry point"

echo ""
echo "=== COMMIT 8: Scripts Consolidation & Updates ==="
git add scripts/run_all.sh scripts/run_demo.sh scripts/reset_database.sh
git rm scripts/mutate.py scripts/observe.py
git commit -m "refactor: consolidate shell scripts and remove python script redirects

New/Updated Scripts:
- scripts/run_all.sh: Complete pipeline automation (up → seed → build → snapshot)
- scripts/run_demo.sh: Multi-domain demonstration with mutations and dbt builds
- scripts/reset_database.sh: Clean database reset with OLTP reinitialization

Removed Redirects:
- scripts/mutate.py: Logic moved to portfolio_api.cli module
- scripts/observe.py: Logic moved to portfolio_api.observe module"

echo ""
echo "=== COMMIT 9: Makefile - DRY Target Consolidation ==="
git add Makefile
git commit -m "feat: add Makefile with consolidated generic targets

- Generic targets: 'build' and 'mutate' with domain parameter
- Domain-specific shortcuts: build-varejo, build-biblioteca, build-rede
- Mutation shortcuts: mutate-varejo, mutate-biblioteca, mutate-rede
- Observation target: observe with domain and cmd parameters
- Full pipeline targets: up, down, reset, run-all, demo
- Removed duplicate build-rede target definition
- Follow DRY principle: single implementation point for each operation"

echo ""
echo "=== GIT LOG - Final Commit History ==="
git log --oneline -15

echo ""
echo "=== STAGING STATUS ==="
git status --short

echo ""
echo "=== READY TO PUSH ==="
echo "Run: git push origin main"
