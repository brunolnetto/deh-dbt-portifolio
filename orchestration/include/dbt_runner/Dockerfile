# Execution image for Cosmos ExecutionMode.DOCKER — bundles the full ecommerce/
# dbt project + profiles.yml so every dbt node runs in an isolated, reproducible
# container. Rebuild whenever the dbt project changes:
#   docker build -t deh-dbt-runner:latest -f orchestration/include/dbt_runner/Dockerfile .
FROM python:3.12-slim

RUN pip install --no-cache-dir "dbt-postgres~=1.8.0"

WORKDIR /usr/app/ecommerce
COPY ecommerce/ .

ENV DBT_PROFILES_DIR=/usr/app/ecommerce
