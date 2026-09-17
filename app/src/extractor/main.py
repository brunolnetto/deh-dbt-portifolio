"""Extractor main loop — dlt loads OLTP API data to PostgreSQL landing + RustFS Parquet archive."""
import asyncio
import logging
import os

import dlt
from dlt.destinations import filesystem, postgres

from .config import (
    EXTRACT_INTERVAL,
    LANDING_BUCKET,
    OLTP_API_URL,
    POSTGRES_DSN,
    RUSTFS_ACCESS_KEY,
    RUSTFS_ENDPOINT,
    RUSTFS_SECRET_KEY,
)
from .pipeline import DOMAINS, oltp_source

log = logging.getLogger(__name__)


def _configure_s3_env() -> None:
    """Expose RustFS credentials as standard AWS env vars consumed by dlt filesystem."""
    os.environ.setdefault("AWS_ACCESS_KEY_ID", RUSTFS_ACCESS_KEY)
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", RUSTFS_SECRET_KEY)
    os.environ.setdefault("AWS_ENDPOINT_URL", f"http://{RUSTFS_ENDPOINT}")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


def _run_cycle() -> None:
    pg_dest = postgres(credentials=POSTGRES_DSN)
    fs_dest = filesystem(bucket_url=f"s3://{LANDING_BUCKET}")

    for domain in DOMAINS:
        pg_pipeline = dlt.pipeline(
            pipeline_name=f"{domain}_pg",
            destination=pg_dest,
            dataset_name=f"landing_{domain}",
        )
        info = pg_pipeline.run(oltp_source(domain, OLTP_API_URL))
        log.info("[%s → postgres] %s", domain, info)

        fs_pipeline = dlt.pipeline(
            pipeline_name=f"{domain}_fs",
            destination=fs_dest,
            dataset_name=domain,
        )
        info = fs_pipeline.run(
            oltp_source(domain, OLTP_API_URL),
            loader_file_format="parquet",
        )
        log.info("[%s → filesystem] %s", domain, info)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    _configure_s3_env()
    log.info("dlt extractor started. OLTP=%s  interval=%ds", OLTP_API_URL, EXTRACT_INTERVAL)
    while True:
        try:
            await asyncio.to_thread(_run_cycle)
            log.info("Extraction cycle complete.")
        except Exception as exc:
            log.error("Extraction cycle failed: %s", exc, exc_info=True)
        await asyncio.sleep(EXTRACT_INTERVAL)
