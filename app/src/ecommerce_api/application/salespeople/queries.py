from datetime import date

from ...domain.salespeople.entities import Salesperson, SalespersonMetrics
from ...domain.salespeople.repository import AbstractSalespersonRepository


class SalespersonQueries:
    def __init__(self, repo: AbstractSalespersonRepository) -> None:
        self._repo = repo

    async def list_salespeople(self) -> list[Salesperson]:
        return await self._repo.list_salespeople()

    async def get_metrics(
        self,
        salesperson_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> SalespersonMetrics:
        return await self._repo.get_metrics(
            salesperson_id=salesperson_id,
            start_date=start_date,
            end_date=end_date,
        )
