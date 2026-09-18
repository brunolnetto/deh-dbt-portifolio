"""Shared helpers for recording pipeline run events — used by the dlt ingestion,
dbt transform, and log-export DAGs.

Two sinks, one per concern:
  - `log_pipeline_event`: one structured row per run into system.app_log
    (same Postgres instance dbt reads from — see stg_app_logs / mart_pipeline_runs).
  - `archive_log_to_blob`: the raw/full log text, archived to RustFS (S3-compatible)
    for audit/debugging, mirroring how domain data lands in blob storage.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import psycopg
from airflow.hooks.base import BaseHook
from airflow.models import Variable

POSTGRES_CONN_ID = "portfolio_postgres"


def _pg_dsn() -> str:
    conn = BaseHook.get_connection(POSTGRES_CONN_ID)
    return (
        f"postgresql://{conn.login}:{conn.password}"
        f"@{conn.host}:{conn.port}/{conn.schema}"
    )


def log_pipeline_event(
    service: str,
    message: str,
    *,
    level: str = "INFO",
    logger: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Insert one row into system.app_log — consumed by dbt (stg_app_logs)."""
    with psycopg.connect(_pg_dsn()) as conn:
        conn.execute(
            "INSERT INTO system.app_log (service, level, logger, message, extra) "
            "VALUES (%s, %s, %s, %s, %s)",
            [service, level, logger, message, json.dumps(extra or {})],
        )
        conn.commit()


def archive_log_to_blob(bucket: str, key: str, content: str) -> str:
    """Upload raw pipeline log text to RustFS (S3-compatible). Returns s3:// URI."""
    import boto3
    from botocore.exceptions import ClientError

    endpoint = Variable.get("RUSTFS_ENDPOINT", default_var="rustfs:9000")
    access_key = Variable.get("RUSTFS_ACCESS_KEY", default_var="minioadmin")
    secret_key = Variable.get("RUSTFS_SECRET_KEY", default_var="minioadmin")

    client = boto3.client(
        "s3",
        endpoint_url=f"http://{endpoint}",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        client.create_bucket(Bucket=bucket)
    except ClientError:
        pass  # bucket already exists

    client.put_object(Bucket=bucket, Key=key, Body=content.encode("utf-8"))
    return f"s3://{bucket}/{key}"


def timestamped_key(prefix: str, extension: str = "log") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y/%m/%d/%H%M%S")
    return f"{prefix}/{stamp}.{extension}"
