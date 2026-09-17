.DEFAULT_GOAL := help

DBT_DIR       := ecommerce
PROFILES_DIR  := ~/.dbt

.PHONY: help up down reset dbt-build dbt-test dbt-snapshot dbt-seed \
        api-build api-up run-all demo

help:
	@echo "Portfolio DEH — Comandos disponíveis:"
	@echo ""
	@echo "  Infraestrutura:"
	@echo "    make up           — Sobe o PostgreSQL + API (Docker Compose)"
	@echo "    make down         — Para e remove os containers"
	@echo "    make reset        — Reinicia o banco do zero"
	@echo ""
	@echo "  dbt:"
	@echo "    make dbt-seed     — Carrega seeds (estados_brasil)"
	@echo "    make dbt-build    — Roda todos os modelos dos 3 domínios"
	@echo "    make dbt-test     — Executa os testes de dados"
	@echo "    make dbt-snapshot — Executa snapshots SCD Tipo 2"
	@echo ""
	@echo "  Mutações OLTP:"
	@echo "    make mutate-varejo     cmd=insert-venda"
	@echo "    make mutate-biblioteca cmd=insert-emprestimo"
	@echo "    make mutate-rede       cmd=insert-leitura"
	@echo ""
	@echo "  Observação BEFORE/AFTER:"
	@echo "    make observe domain=varejo     cmd=insert-venda"
	@echo "    make observe domain=biblioteca cmd=insert-emprestimo"
	@echo "    make observe domain=rede_social cmd=insert-leitura --no-dbt"
	@echo ""
	@echo "  Domínios dbt (tag filter):"
	@echo "    make build-varejo     — Só modelos varejo"
	@echo "    make build-biblioteca — Só modelos biblioteca"
	@echo "    make build-rede       — Só modelos rede_social"

# ── Infraestrutura ─────────────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up -d
	@echo "Aguardando banco de dados..."
	@sleep 5
	$(MAKE) dbt-seed dbt-build

# ── dbt ───────────────────────────────────────────────────────────────────

dbt-seed:
	cd $(DBT_DIR) && dbt seed --profiles-dir $(PROFILES_DIR)

dbt-build:
	cd $(DBT_DIR) && dbt build --profiles-dir $(PROFILES_DIR)

dbt-test:
	cd $(DBT_DIR) && dbt test --profiles-dir $(PROFILES_DIR)

dbt-snapshot:
	cd $(DBT_DIR) && dbt snapshot --profiles-dir $(PROFILES_DIR)

# ── Build por Domínio (delegando ao target genérico) ────────────────────

build:
	cd $(DBT_DIR) && dbt build --profiles-dir $(PROFILES_DIR) --select tag:$(domain)

build-varejo:
	$(MAKE) build domain=varejo

build-biblioteca:
	$(MAKE) build domain=biblioteca

build-rede:
	$(MAKE) build domain=rede_social

# ── Mutações OLTP ─────────────────────────────────────────────────────────

mutate:
	python -m portfolio_api.cli $(domain) $(cmd)

mutate-varejo:
	$(MAKE) mutate domain=varejo cmd=$(cmd)

mutate-biblioteca:
	$(MAKE) mutate domain=biblioteca cmd=$(cmd)

mutate-rede:
	$(MAKE) mutate domain=rede_social cmd=$(cmd)

observe:
	python -m portfolio_api.observe $(domain) $(cmd)

# ── Pipeline completo ─────────────────────────────────────────────────────

run-all: up
	@sleep 5
	$(MAKE) dbt-seed dbt-build dbt-snapshot

demo:
	bash scripts/run_demo.sh
