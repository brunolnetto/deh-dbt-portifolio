"""Rede Social domain queries against analytics_rede_social schema."""

from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


class RedeSocialRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_pessoas(self, limit: int = 50) -> list[dict[str, Any]]:
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT pessoa_id, person_name, age,
                           total_books_read, avg_rating, preferred_genres
                    FROM analytics_rede_social.dim_pessoas
                    ORDER BY total_books_read DESC
                    LIMIT $1
                    """,
                    [limit],
                )
                return await cur.fetchall()

    async def list_leituras(
        self,
        pessoa_id: int | None = None,
        livro_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if pessoa_id:
            conditions.append(f"l.pessoa_id = ${len(params) + 1}")
            params.append(pessoa_id)
        if livro_id:
            conditions.append(f"l.livro_id = ${len(params) + 1}")
            params.append(livro_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    f"""
                    SELECT l.pessoa_id, p.person_name, l.livro_id, lr.title,
                           lr.author, l.rating, l.read_date
                    FROM analytics_rede_social.fct_leituras l
                    JOIN analytics_rede_social.dim_pessoas p ON l.pessoa_id = p.pessoa_id
                    JOIN analytics_rede_social.dim_livros_rede lr ON l.livro_id = lr.livro_id
                    {where}
                    ORDER BY l.read_date DESC
                    LIMIT ${len(params)}
                    """,
                    params,
                )
                return await cur.fetchall()

    async def get_recomendacoes(self, pessoa_id: int) -> list[dict[str, Any]]:
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT pessoa_id, person_name, livro_id, title, author,
                           network_avg_rating, network_readers,
                           avg_connection_strength, recommended_by_count
                    FROM analytics_rede_social.mart_recomendacoes
                    WHERE pessoa_id = $1
                    ORDER BY network_avg_rating DESC, recommended_by_count DESC
                    LIMIT 10
                    """,
                    [pessoa_id],
                )
                return await cur.fetchall()

    async def get_dashboard(self) -> dict[str, Any]:
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT
                        count(distinct pessoa_id)               as total_people,
                        count(distinct livro_id)                as total_books,
                        count(*)                                as total_readings,
                        round(avg(rating)::numeric, 2)          as avg_rating,
                        (SELECT count(*) FROM analytics_rede_social.fct_conexoes)
                                                                as total_connections
                    FROM analytics_rede_social.fct_leituras
                    """
                )
                row = await cur.fetchone()
                return row or {}
    async def list_pessoas(self, limit: int = 50) -> list[dict[str, Any]]:
        return await run_query(
            """
            SELECT pessoa_id, person_name, age,
                   total_books_read, avg_rating, preferred_genres
            FROM analytics_rede_social.dim_pessoas
            ORDER BY total_books_read DESC
            LIMIT ?
            """,
            [limit],
        )

    async def list_leituras(
        self,
        pessoa_id: int | None = None,
        livro_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if pessoa_id:
            conditions.append("l.pessoa_id = ?")
            params.append(pessoa_id)
        if livro_id:
            conditions.append("l.livro_id = ?")
            params.append(livro_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)
        return await run_query(
            f"""
            SELECT l.pessoa_id, p.person_name, l.livro_id, lr.title,
                   lr.author, l.rating, l.read_date
            FROM analytics_rede_social.fct_leituras l
            JOIN analytics_rede_social.dim_pessoas p ON l.pessoa_id = p.pessoa_id
            JOIN analytics_rede_social.dim_livros_rede lr ON l.livro_id = lr.livro_id
            {where}
            ORDER BY l.read_date DESC
            LIMIT ?
            """,
            params,
        )

    async def get_recomendacoes(self, pessoa_id: int) -> list[dict[str, Any]]:
        return await run_query(
            """
            SELECT pessoa_id, person_name, livro_id, title, author,
                   network_avg_rating, network_readers,
                   avg_connection_strength, recommended_by_count
            FROM analytics_rede_social.mart_recomendacoes
            WHERE pessoa_id = ?
            ORDER BY network_avg_rating DESC, recommended_by_count DESC
            LIMIT 10
            """,
            [pessoa_id],
        )

    async def get_dashboard(self) -> dict[str, Any]:
        return await run_query_one(
            """
            SELECT
                count(distinct pessoa_id)               as total_people,
                count(distinct livro_id)                as total_books,
                count(*)                                as total_readings,
                round(avg(rating)::numeric, 2)          as avg_rating,
                (SELECT count(*) FROM analytics_rede_social.fct_conexoes)
                                                        as total_connections
            FROM analytics_rede_social.fct_leituras
            """
        )

    async def list_pessoas(self, limit: int = 50) -> list[dict[str, Any]]:
        async with self._pool.connection() as conn:
            rows = await conn.execute(
                """
                SELECT pessoa_id, person_name, age,
                       total_books_read, avg_rating, preferred_genres
                FROM analytics_rede_social.dim_pessoas
                ORDER BY total_books_read DESC
                LIMIT $1
                """,
                [limit],
            )
            return [dict(row) async for row in rows]

    async def list_leituras(
        self,
        pessoa_id: int | None = None,
        livro_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if pessoa_id:
            conditions.append(f"l.pessoa_id = ${len(params) + 1}")
            params.append(pessoa_id)
        if livro_id:
            conditions.append(f"l.livro_id = ${len(params) + 1}")
            params.append(livro_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT l.pessoa_id, p.person_name, l.livro_id, lr.title,
                       lr.author, l.rating, l.read_date
                FROM analytics_rede_social.fct_leituras l
                JOIN analytics_rede_social.dim_pessoas p ON l.pessoa_id = p.pessoa_id
                JOIN analytics_rede_social.dim_livros_rede lr ON l.livro_id = lr.livro_id
                {where}
                ORDER BY l.read_date DESC
                LIMIT ${len(params)}
                """,
                params,
            )
            return [dict(row) async for row in rows]

    async def get_recomendacoes(self, pessoa_id: int) -> list[dict[str, Any]]:
        async with self._pool.connection() as conn:
            rows = await conn.execute(
                """
                SELECT pessoa_id, person_name, livro_id, title, author,
                       network_avg_rating, network_readers,
                       avg_connection_strength, recommended_by_count
                FROM analytics_rede_social.mart_recomendacoes
                WHERE pessoa_id = $1
                ORDER BY network_avg_rating DESC, recommended_by_count DESC
                LIMIT 10
                """,
                [pessoa_id],
            )
            return [dict(row) async for row in rows]

    async def get_dashboard(self) -> dict[str, Any]:
        async with self._pool.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    count(distinct pessoa_id)               as total_people,
                    count(distinct livro_id)                as total_books,
                    count(*)                                as total_readings,
                    round(avg(rating)::numeric, 2)          as avg_rating,
                    (SELECT count(*) FROM analytics_rede_social.fct_conexoes)
                                                            as total_connections
                FROM analytics_rede_social.fct_leituras
                """
            )
            return dict(row) if row else {}
