from abc import ABC, abstractmethod
from datetime import date

from .entities import Salesperson, SalespersonMetrics


class AbstractSalespersonRepository(ABC):
    @abstractmethod
    async def list_salespeople(self) -> list[Salesperson]: ...

    @abstractmethod
    async def get_metrics(
        self,
        salesperson_id: int | None,
        start_date: date | None,
        end_date: date | None,
    ) -> SalespersonMetrics: ...
