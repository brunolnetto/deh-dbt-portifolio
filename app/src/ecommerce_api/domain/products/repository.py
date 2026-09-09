from abc import ABC, abstractmethod
from datetime import date

from .entities import Product, ProductMetrics, ProductPerformance


class AbstractProductRepository(ABC):
    @abstractmethod
    async def list_products(
        self,
        category: str | None,
        is_active: bool | None,
        limit: int,
    ) -> list[Product]: ...

    @abstractmethod
    async def get_performance(
        self,
        category: str | None,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> list[ProductPerformance]: ...

    @abstractmethod
    async def get_metrics(
        self,
        product_id: int | None,
        start_date: date | None,
        end_date: date | None,
    ) -> ProductMetrics: ...
