"""One-shot ingestion entry point for Airflow-triggered runs.

`python -m extractor` runs an infinite polling loop (for docker-compose standalone
use). Airflow instead schedules single extraction cycles via Cosmos-adjacent
DockerOperator tasks, so this module runs exactly one cycle and exits.
"""
import logging

from .config import OLTP_API_URL
from .main import _configure_s3_env, _run_cycle

log = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    _configure_s3_env()
    log.info("dlt one-shot extraction started. OLTP=%s", OLTP_API_URL)
    _run_cycle()
    log.info("Extraction cycle complete.")


if __name__ == "__main__":
    main()
