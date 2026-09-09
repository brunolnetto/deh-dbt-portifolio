from psycopg_pool import AsyncConnectionPool

_pool: AsyncConnectionPool | None = None


def get_pool() -> AsyncConnectionPool:
    assert _pool is not None, "DB pool not initialized; ensure lifespan ran."
    return _pool


async def init_pool(dsn: str) -> None:
    global _pool
    if _pool is not None:
        return
    _pool = AsyncConnectionPool(conninfo=dsn, open=False)
    await _pool.open()


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
