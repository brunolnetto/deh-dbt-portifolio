"""Pipeline log export DAG — archives Airflow task logs to blob storage (RustFS)
and records a structured summary in system.app_log for every dbt_transform /
dlt_ingestion run, so pipeline observability flows through the same dbt models
as the OLTP/analytics API request logs (stg_app_logs -> mart_pipeline_runs).

Triggered by `on_success_callback` / `on_failure_callback` wiring would require
editing the other DAGs directly; instead this DAG polls recently completed runs
of dbt_transform and dlt_ingestion via the Airflow API/DB on a short schedule,
which keeps the source DAGs (and Cosmos' generated one) untouched.
"""
from __future__ import annotations

import os

from airflow.decorators import dag, task
from pendulum import datetime

MONITORED_DAG_IDS = ["dbt_transform", "dlt_ingestion"]
PIPELINE_LOG_BUCKET = os.getenv("PIPELINE_LOG_BUCKET", "pipeline-logs")
WATERMARK_VARIABLE = "pipeline_log_export_watermark"


@dag(
    dag_id="pipeline_log_export",
    schedule="*/15 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 1},
    tags=["observability", "logs"],
)
def pipeline_log_export():
    @task
    def export_recent_runs() -> None:
        from airflow.models import DagRun, TaskInstance, Variable
        from airflow.utils.session import create_session
        from airflow.utils.state import State

        from include.pipeline_logging import (
            archive_log_to_blob,
            log_pipeline_event,
            timestamped_key,
        )

        watermark = Variable.get(WATERMARK_VARIABLE, default_var="1900-01-01T00:00:00+00:00")
        latest_seen = watermark

        with create_session() as session:
            task_instances = (
                session.query(TaskInstance)
                .join(DagRun, TaskInstance.run_id == DagRun.run_id)
                .filter(
                    TaskInstance.dag_id.in_(MONITORED_DAG_IDS),
                    TaskInstance.state.in_([State.SUCCESS, State.FAILED]),
                    TaskInstance.end_date > watermark,
                )
                .order_by(TaskInstance.end_date.asc())
                .limit(200)
                .all()
            )

            for ti in task_instances:
                try:
                    # Note: fetching the *full* log body requires Airflow's
                    # TaskLogReader (remote logging config). This example ships
                    # a summary + pointer to keep the DAG dependency-free; wire
                    # in TaskLogReader here for a production deployment.
                    log_text = (
                        f"dag_id={ti.dag_id} task_id={ti.task_id} run_id={ti.run_id} "
                        f"state={ti.state} try_number={ti.try_number}"
                    )
                    blob_key = timestamped_key(f"{ti.dag_id}/{ti.task_id}", extension="log")
                    blob_path = archive_log_to_blob(PIPELINE_LOG_BUCKET, blob_key, log_text)

                    duration_s = (
                        (ti.end_date - ti.start_date).total_seconds()
                        if ti.start_date and ti.end_date
                        else None
                    )
                    log_pipeline_event(
                        service="airflow-dbt" if ti.dag_id == "dbt_transform" else "airflow-dlt",
                        level="INFO" if ti.state == State.SUCCESS else "ERROR",
                        logger="pipeline_log_export_dag",
                        message=f"{ti.dag_id}.{ti.task_id} finished with state={ti.state}",
                        extra={
                            "dag_id": ti.dag_id,
                            "task_id": ti.task_id,
                            "run_id": ti.run_id,
                            "duration_s": duration_s,
                            "blob_path": blob_path,
                        },
                    )
                    latest_seen = ti.end_date.isoformat()
                except Exception as exc:  # never fail the whole export over one bad row
                    print(f"log export failed for {ti.dag_id}.{ti.task_id}: {exc}")

        if latest_seen != watermark:
            Variable.set(WATERMARK_VARIABLE, latest_seen)

    export_recent_runs()


pipeline_log_export()
