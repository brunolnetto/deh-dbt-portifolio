from datetime import date

from ...domain.products.entities import Product, ProductMetrics, ProductPerformance
from ...domain.products.repository import AbstractProductRepository


class ProductQueries:
    def __init__(self, repo: AbstractProductRepository) -> None:
        self._repo = repo

    async def list_products(
        self,
        category: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
    ) -> list[Product]:
        return await self._repo.list_products(
            category=category,
            is_active=is_active,
            limit=limit,
        )

    async def get_performance(
        self,
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 50,
    ) -> list[ProductPerformance]:
        return await self._repo.get_performance(
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    async def get_metrics(
        self,
        product_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> ProductMetrics:
        return await self._repo.get_metrics(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
        )
