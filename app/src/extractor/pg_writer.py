"""Write extracted records to PostgreSQL landing schemas (full-refresh per cycle)."""
import logging

import psycopg
from psycopg import sql

from .config import POSTGRES_DSN

log = logging.getLogger(__name__)


async def write_to_landing(records: list[dict], schema: str, table: str) -> int:
    """TRUNCATE + bulk-INSERT records into the landing schema table.

    Returns number of records written (0 if records is empty).
    """
    if not records:
        log.debug("[landing/%s.%s] No records — skipping.", schema, table)
        return 0

    cols = list(records[0].keys())
    values = [[r.get(c) for c in cols] for r in records]

    async with await psycopg.AsyncConnection.connect(POSTGRES_DSN) as conn:
        await conn.execute(
            sql.SQL("TRUNCATE {}.{}").format(
                sql.Identifier(schema), sql.Identifier(table)
            )
        )
        async with conn.cursor() as cur:
            await cur.executemany(
                sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                    sql.Identifier(schema),
                    sql.Identifier(table),
                    sql.SQL(", ").join(map(sql.Identifier, cols)),
                    sql.SQL(", ").join([sql.Placeholder()] * len(cols)),
                ),
                values,
            )
        await conn.commit()

    log.info("[landing/%s.%s] Wrote %d records", schema, table, len(records))
    return len(records)
