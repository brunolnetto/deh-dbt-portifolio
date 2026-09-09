from abc import ABC, abstractmethod
from datetime import date

from .entities import Order, OrderMetrics


class AbstractOrderRepository(ABC):
    @abstractmethod
    async def list_orders(
        self,
        status: str | None,
        start_date: date | None,
        end_date: date | None,
        customer_id: int | None,
        salesperson_id: int | None,
        limit: int,
    ) -> list[Order]: ...

    @abstractmethod
    async def get_metrics(
        self,
        status: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> OrderMetrics: ...
