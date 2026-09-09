from ...application.orders.queries import OrderQueries
from ...application.products.queries import ProductQueries
from ...application.salespeople.queries import SalespersonQueries
from ...infrastructure.database import get_pool
from ...infrastructure.orders.repository import PostgresOrderRepository
from ...infrastructure.products.repository import PostgresProductRepository
from ...infrastructure.salespeople.repository import PostgresSalespersonRepository


def get_order_queries() -> OrderQueries:
    return OrderQueries(PostgresOrderRepository(get_pool()))


def get_product_queries() -> ProductQueries:
    return ProductQueries(PostgresProductRepository(get_pool()))


def get_salesperson_queries() -> SalespersonQueries:
    return SalespersonQueries(PostgresSalespersonRepository(get_pool()))
