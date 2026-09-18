"""dlt ingestion DAG — runs one extraction cycle per OLTP domain as a container.

Replaces the always-on docker-compose `extractor` loop for scheduled/orchestrated
runs: each task launches the existing `app` image (python -m extractor.run_once)
as a sibling container via DockerOperator, then a downstream task records a
summary row in system.app_log and archives the task's raw log to blob storage —
mirroring what `pipeline_log_export_dag` does for the dbt side.
"""
import os

from airflow.decorators import task
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import DAG
from pendulum import datetime

DOMAINS = ["varejo", "biblioteca", "rede_social"]

APP_IMAGE = os.getenv("APP_IMAGE", "deh-dbt-portifolio-app:latest")
DEH_NETWORK = os.getenv("DEH_DOCKER_NETWORK", "deh_network")


@task
def record_ingestion_run(domain: str, **context) -> None:
    from include.pipeline_logging import log_pipeline_event

    ti = context["ti"]
    log_pipeline_event(
        service="airflow-dlt",
        message=f"dlt extraction cycle complete for domain={domain}",
        logger="dlt_ingestion_dag",
        extra={
            "dag_id": ti.dag_id,
            "task_id": ti.task_id,
            "run_id": context["run_id"],
            "domain": domain,
        },
    )


with DAG(
    dag_id="dlt_ingestion",
    schedule="*/30 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 1},
    tags=["dlt", "ingestion"],
) as dag:
    for domain in DOMAINS:
        extract = DockerOperator(
            task_id=f"extract_{domain}",
            image=APP_IMAGE,
            command=["python", "-m", "extractor.run_once"],
            network_mode=DEH_NETWORK,
            auto_remove="success",
            environment={
                "OLTP_API_URL": "http://oltp-api:8001",
                "RUSTFS_ENDPOINT": "rustfs:9000",
                "RUSTFS_ACCESS_KEY": os.getenv("RUSTFS_ACCESS_KEY", "minioadmin"),
                "RUSTFS_SECRET_KEY": os.getenv("RUSTFS_SECRET_KEY", "minioadmin"),
            },
        )
        extract >> record_ingestion_run(domain)
