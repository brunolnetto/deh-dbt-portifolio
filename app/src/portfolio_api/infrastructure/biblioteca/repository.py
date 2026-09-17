"""Biblioteca domain queries against analytics_biblioteca schema."""

from typing import Any

from psycopg_pool import AsyncConnectionPool


class BibliotecaRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_livros(
        self,
        available_only: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        where = "WHERE available_copies > 0" if available_only else ""
        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT livro_id, title, isbn, publication_year,
                       available_copies, authors, total_loans, active_loans
                FROM analytics_biblioteca.dim_livros
                {where}
                ORDER BY title
                LIMIT $1
                """,
                [limit],
            )
            return [dict(row) async for row in rows]

    async def list_usuarios(
        self,
        user_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if user_type:
            conditions.append(f"user_type = ${len(params) + 1}")
            params.append(user_type)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT usuario_id, user_name, user_type, email,
                       total_loans, active_loans, overdue_loans, total_fines
                FROM analytics_biblioteca.mart_usuario_emprestimos
                {where}
                ORDER BY user_name
                LIMIT ${len(params)}
                """,
                params,
            )
            return [dict(row) async for row in rows]

    async def list_emprestimos(
        self,
        is_overdue: bool | None = None,
        usuario_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions, params = [], []
        if is_overdue is not None:
            conditions.append(f"is_overdue = ${len(params) + 1}")
            params.append(is_overdue)
        if usuario_id:
            conditions.append(f"usuario_id = ${len(params) + 1}")
            params.append(usuario_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        async with self._pool.connection() as conn:
            rows = await conn.execute(
                f"""
                SELECT emprestimo_id, usuario_id, livro_id, loan_date,
                       due_date, return_date, is_returned, is_overdue,
                       days_overdue, fine_amount, fine_paid
                FROM analytics_biblioteca.fct_emprestimos
                {where}
                ORDER BY loan_date DESC
                LIMIT ${len(params)}
                """,
                params,
            )
            return [dict(row) async for row in rows]

    async def get_dashboard(self) -> dict[str, Any]:
        async with self._pool.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    count(distinct livro_id)                        as total_books,
                    count(distinct usuario_id)                      as total_users,
                    count(*)                                        as total_loans,
                    sum(case when is_returned then 1 end)           as returned_loans,
                    sum(case when not is_returned then 1 end)       as active_loans,
                    sum(case when is_overdue then 1 end)            as overdue_loans,
                    coalesce(sum(fine_amount), 0)                   as total_fines_issued,
                    coalesce(sum(case when fine_paid then fine_amount end), 0) as fines_paid
                FROM analytics_biblioteca.fct_emprestimos
                """
            )
            return dict(row) if row else {}
