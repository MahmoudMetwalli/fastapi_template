from uuid import uuid4

import pytest

from app.contexts.ordering.application.queries import GetOrderQuery
from app.contexts.ordering.application.use_cases.get_order import GetOrderUseCase
from app.contexts.ordering.domain.errors import OrderNotFoundError
from app.contexts.ordering.domain.order import Order
from app.contexts.ordering.domain.value_objects import OrderLine, Quantity
from tests.factories import make_ordered_book_snapshot
from tests.fakes import InMemoryOrderRepository


@pytest.fixture
def orders() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()


class TestGetOrder:
    async def test_returns_the_order_with_its_lines(self, orders: InMemoryOrderRepository) -> None:
        order = Order.place(
            lines=[
                OrderLine(
                    snapshot=make_ordered_book_snapshot(title="Refactoring", unit_price_cents=2999),
                    quantity=Quantity(2),
                )
            ]
        )
        await orders.add(order)
        use_case = GetOrderUseCase(orders=orders)

        read_model = await use_case.execute(GetOrderQuery(order_id=order.id.value))

        assert read_model.total_cents == 5998
        assert read_model.lines[0].title == "Refactoring"
        assert read_model.lines[0].subtotal_cents == 5998

    async def test_raises_for_an_unknown_id(self, orders: InMemoryOrderRepository) -> None:
        use_case = GetOrderUseCase(orders=orders)
        with pytest.raises(OrderNotFoundError):
            await use_case.execute(GetOrderQuery(order_id=uuid4()))
