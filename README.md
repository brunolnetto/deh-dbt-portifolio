# Portfolio DEH — Multi-Domain Analytics Platform

Plataforma analítica de produção para **3 domínios independentes** (Varejo, Biblioteca, Rede Social) com dbt, FastAPI, PostgreSQL e integração MCP para Claude.

Este projeto demonstra padrões avançados de data engineering e analytics:
- **Multi-domínio com isolamento de schema** via macros dbt
- **Arquitetura em 3 camadas**: staging → intermediate → marts
- **REST API** com endpoints específicos por domínio
- **MCP tools** para integração com Claude
- **OLTP mutations** via sidecar e CLI
- **Observação BEFORE/AFTER** com snapshots automáticos
- **CI/CD** com validação de builds por domínio

---

## 📊 Domínios (Domains)

### 1. **Varejo** (Retail E-Commerce)
- **OLTP Tables**: origen_cliente, origin_produto, origin_venda
- **Staging Models**: stg_clientes, stg_produtos, stg_vendas
- **Marts**: dim_clientes, dim_produtos, fct_vendas (incremental), mart_clientes_vendas
- **Analytics**: Customers, products, sales by segment/state, revenue trends
- **Snapshot**: clientes_snapshot (SCD Type 2 on segmento changes)

### 2. **Biblioteca** (Library Management)
- **OLTP Tables**: usuario, livro, emprestimo, multa, autor, livro_autor
- **Staging Models**: stg_usuarios, stg_livros, stg_emprestimos, stg_autores
- **Marts**: dim_livros, dim_usuarios, fct_emprestimos (incremental), mart_usuario_emprestimos
- **Analytics**: Books inventory, user loans, overdue tracking, fines, author popularity
- **Tracking**: Late returns, automatic fines calculation

### 3. **Rede Social** (Social Reading Network)
- **OLTP Tables**: pessoa, livro, leitura, conexao_social, genero, pessoa_preferencia
- **Staging Models**: stg_pessoas, stg_leituras, stg_conexoes, stg_generos
- **Marts**: dim_pessoas, dim_livros_rede, fct_leituras, fct_conexoes, mart_recomendacoes
- **Analytics**: Reading ratings, social connections, personalized recommendations
- **Graph Analytics**: Social connection strength, community detection

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- Python 3.13+
- dbt-core, dbt-postgres
- PostgreSQL client (psql)

### 1. Start Infrastructure

```bash
make up           # Spin up postgres + api + mutator
sleep 5
make dbt-seed     # Load seeds (estados_brasil.csv)
make dbt-build    # Build all 3 domain models
```

### 2. Verify API

```bash
# REST Endpoints
curl http://localhost:8000/api/v1/varejo/dashboard
curl http://localhost:8000/api/v1/biblioteca/dashboard
curl http://localhost:8000/api/v1/rede_social/dashboard
```

### 3. Run Demo

```bash
make demo         # Multi-domain demonstration with mutations
```

---

## 📁 Project Structure

- **oltp/init.sql** - OLTP schemas for 3 domains
- **ecommerce/** - dbt project (portfolio)
  - **models/staging/** - Raw data models
  - **models/intermediate/** - Enrichment & aggregations
  - **models/mart/** - Analytics dimensions & facts
  - **snapshots/** - SCD Type 2 (clientes_snapshot)
  - **seeds/** - Reference data
- **app/src/portfolio_api/** - FastAPI application
  - **infrastructure/** - Repositories per domain
  - **presentation/api/** - REST endpoints
  - **presentation/mcp/** - Claude integration tools
  - **mutator.py** - Async mutation sidecar
  - **cli.py** - Manual CLI mutations
  - **observe.py** - BEFORE/AFTER observation
- **scripts/** - Automation scripts
- **Makefile** - DRY command targets
- **docker-compose.yml** - Services orchestration
- **.github/workflows/dbt-ci.yml** - CI/CD pipeline

---

## 🔌 REST API Endpoints

| Domain | Endpoint | Description |
|--------|----------|-------------|
| Varejo | GET /api/v1/varejo/clientes | List customers |
| Varejo | GET /api/v1/varejo/produtos | List products |
| Varejo | GET /api/v1/varejo/vendas | List sales |
| Varejo | GET /api/v1/varejo/dashboard | Sales metrics |
| Biblioteca | GET /api/v1/biblioteca/livros | List books |
| Biblioteca | GET /api/v1/biblioteca/usuarios | List users |
| Biblioteca | GET /api/v1/biblioteca/emprestimos | List loans |
| Biblioteca | GET /api/v1/biblioteca/dashboard | Library metrics |
| Rede Social | GET /api/v1/rede_social/pessoas | List people |
| Rede Social | GET /api/v1/rede_social/leituras | List readings |
| Rede Social | GET /api/v1/rede_social/recomendacoes/{pessoa_id} | Recommendations |
| Rede Social | GET /api/v1/rede_social/dashboard | Network metrics |

---

## 🤖 MCP Tools (Claude Integration)

8 tools available for Claude via POST /mcp:
- get_varejo_dashboard, list_varejo_clientes
- get_biblioteca_dashboard, list_biblioteca_livros
- get_rede_social_dashboard, list_rede_social_leituras, get_recomendacoes

---

## 📦 Makefile Commands

### Infrastructure

```bash
make up              # Start services
make down            # Stop services
make reset           # Full reset: down, up, seed, build
```

### dbt

```bash
make dbt-seed        # Load seeds
make dbt-build       # Build all models
make dbt-test        # Run tests
make dbt-snapshot    # Run snapshots
```

### Domain Builds (using generic target)

```bash
make build-varejo
make build-biblioteca
make build-rede
```

### Mutations

```bash
make mutate-varejo cmd=insert-venda
make mutate-biblioteca cmd=return-livro
make mutate-rede cmd=insert-leitura
```

### Observation & Pipelines

```bash
make observe domain=varejo cmd=insert-venda
make run-all         # Full pipeline
make demo            # Comprehensive demo
```

---

## 🔄 OLTP Mutations

### CLI Interface

```bash
python -m portfolio_api.cli varejo insert-venda
python -m portfolio_api.cli biblioteca return-livro
python -m portfolio_api.cli rede_social insert-leitura
```

### Sidecar Service
Automatically runs with \docker compose up\ (MUTATE_INTERVAL=10s)

---

## 🔍 Observation Tool

Snapshots OLTP+Analytics → Mutation → dbt rebuild → After snapshot

```bash
make observe domain=varejo cmd=insert-venda
```

---

## 🚀 CI/CD Pipeline

GitHub Actions validates each domain independently:

```bash
dbt seed
dbt build --select tag:varejo
dbt build --select tag:biblioteca
dbt build --select tag:rede_social
```

---

## 🎯 Key Takeaways

✅ Multi-domain architecture with isolated schemas  
✅ dbt best practices: incremental, snapshots, macros, tests  
✅ Modern Python stack: FastAPI, async, type hints  
✅ Production patterns: repository, pooling, env config  
✅ API integration: REST, MCP, sidecar mutations  
✅ Data observability: BEFORE/AFTER with rebuilds  
✅ Infrastructure as Code: Docker, GitHub Actions, Makefile  

Perfect for multi-tenant analytics platforms.
