from datetime import date

from ...domain.orders.entities import Order, OrderMetrics
from ...domain.orders.repository import AbstractOrderRepository


class OrderQueries:
    def __init__(self, repo: AbstractOrderRepository) -> None:
        self._repo = repo

    async def list_orders(
        self,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        salesperson_id: int | None = None,
        limit: int = 50,
    ) -> list[Order]:
        return await self._repo.list_orders(
            status=status,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            salesperson_id=salesperson_id,
            limit=limit,
        )

    async def get_metrics(
        self,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> OrderMetrics:
        return await self._repo.get_metrics(
            status=status,
            start_date=start_date,
            end_date=end_date,
        )
