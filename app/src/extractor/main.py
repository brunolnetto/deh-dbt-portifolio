"""Extractor main loop — polls OLTP API and writes Parquet to RustFS landing zone."""
import asyncio
import logging

import httpx

from .config import EXTRACT_INTERVAL, OLTP_API_URL
from .domains.biblioteca import extract_biblioteca
from .domains.rede_social import extract_rede_social
from .domains.varejo import extract_varejo

log = logging.getLogger(__name__)


async def _run_cycle(client: httpx.AsyncClient) -> None:
    await extract_varejo(client)
    await extract_biblioteca(client)
    await extract_rede_social(client)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    log.info("Extractor started. OLTP_API=%s  interval=%ds", OLTP_API_URL, EXTRACT_INTERVAL)

    async with httpx.AsyncClient(base_url=OLTP_API_URL, timeout=30.0) as client:
        while True:
            try:
                await _run_cycle(client)
                log.info("Extraction cycle complete.")
            except Exception as exc:
                log.error("Extraction cycle failed: %s", exc)
            await asyncio.sleep(EXTRACT_INTERVAL)
