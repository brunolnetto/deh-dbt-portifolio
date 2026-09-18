# orchestration/ — Airflow (Astro CLI) + Cosmos

Orchestrates the two pipelines that used to run as standalone containers
(`extractor`, and manual `dbt build`/`dbt snapshot` calls) as proper Airflow
DAGs, hosted via the [Astro CLI](https://www.astronomer.io/docs/astro/cli/overview),
with every dbt/dlt task executing in its own disposable Docker container.

## DAGs

| DAG | Schedule | What it does |
|---|---|---|
| `dbt_transform` | hourly | Cosmos-generated DAG — one Airflow task per dbt node (`ecommerce/`), each run in a container built from `include/dbt_runner/`. |
| `dlt_ingestion` | every 30 min | One task per domain (varejo/biblioteca/rede_social), each running `python -m extractor.run_once` in the existing `app` image. |
| `pipeline_log_export` | every 15 min | Archives recently completed `dbt_transform`/`dlt_ingestion` task logs to RustFS (blob storage) and writes a structured summary row to `system.app_log`, which dbt then processes via `stg_app_logs` → `mart_pipeline_runs` — the same pattern already used for OLTP/analytics API request logs (`system.request_log` → `stg_request_logs` → `mart_api_health`). |

## Why containers, and why this shape

- **Astro CLI** hosts Airflow itself as a container (`astro dev start`).
- **Cosmos** (`ExecutionMode.DOCKER`) never runs `dbt` on the Airflow worker —
  each dbt node is dispatched to a *sibling* container (via the mounted
  `docker.sock`), built from `include/dbt_runner/Dockerfile`, which bundles
  `ecommerce/` + `profiles.yml`.
- Cosmos still needs to *parse* the dbt project to build the DAG. Since the
  Airflow image has no dbt installed, parsing uses a pre-generated
  `manifest.json` (`LoadMode.DBT_MANIFEST`) instead of `dbt ls`.

This means the Airflow image stays dbt-free, but requires two things kept in
sync manually:

1. **Regenerate the manifest** whenever `ecommerce/` changes:
   ```
   make dbt-manifest
   ```
2. **Rebuild the dbt runner image** whenever `ecommerce/` changes:
   ```
   docker build -t deh-dbt-runner:latest -f orchestration/include/dbt_runner/Dockerfile .
   ```

## One-time setup

```bash
# 1. Start the shared services (postgres, rustfs) + create the shared network
docker compose up -d postgres rustfs

# 2. Build the images the DAGs launch as sibling containers
docker compose build extractor          # -> deh-dbt-portifolio-app:latest (or set APP_IMAGE)
make dbt-manifest
docker build -t deh-dbt-runner:latest -f orchestration/include/dbt_runner/Dockerfile .

# 3. Set HOST_PROJECT_DIR in orchestration/.env to this repo's absolute HOST path
#    (required because DockerOperator launches sibling containers, not nested ones —
#    bind-mount sources must resolve on the Docker host, not inside the scheduler container)

# 4. Start Airflow
cd orchestration
astro dev start
```

Airflow UI: http://localhost:8080 (default local credentials from Astro CLI).

## Caveats

- Running Airflow itself in a container *and* using `ExecutionMode.DOCKER`
  means DockerOperator launches **sibling** containers via the host's Docker
  engine (not nested Docker-in-Docker) — this is the standard, supported
  Astro + Cosmos recipe, but it does mean every dbt task is a full container
  start/stop, which is slower than `local`/`virtualenv` execution modes. Fine
  for a portfolio/demo project; for higher-frequency production pipelines,
  consider `ExecutionMode.VIRTUALENV` or `KUBERNETES` instead.
- `pipeline_log_export` ships a log **summary + blob pointer**, not the full
  task log body (wiring in Airflow's `TaskLogReader` for full-text export is
  a natural next step, left out here to keep the DAG dependency-free).
