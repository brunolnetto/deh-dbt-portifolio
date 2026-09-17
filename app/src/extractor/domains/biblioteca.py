import logging
from typing import Any

import httpx

from ..pg_writer import write_to_landing
from ..s3_writer import write_parquet

log = logging.getLogger(__name__)

_PAGE = 1000


async def _fetch_all(client: httpx.AsyncClient, path: str) -> list[dict[str, Any]]:
    records, offset = [], 0
    while True:
        resp = await client.get(path, params={"limit": _PAGE, "offset": offset})
        resp.raise_for_status()
        batch: list[dict] = resp.json()
        if not batch:
            break
        records.extend(batch)
        offset += len(batch)
        if len(batch) < _PAGE:
            break
    return records


async def extract_biblioteca(client: httpx.AsyncClient) -> None:
    for entity in ("usuarios", "livros", "emprestimos", "autores", "multas"):
        records = await _fetch_all(client, f"/biblioteca/{entity}")
        write_parquet(records, f"biblioteca/{entity}")                         # S3 archive
        await write_to_landing(records, "landing_biblioteca", entity)         # PostgreSQL
