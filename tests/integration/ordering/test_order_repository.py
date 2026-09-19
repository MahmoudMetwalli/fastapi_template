"""Against real Postgres — proves the one-to-many `Order`/`OrderLine`
mapping round-trips, including `selectinload` actually populating
`order.lines` after the session that loaded it has closed (see
`infrastructure/persistence/order_repository.py`).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.ordering.domain.order import Order, OrderId
from app.contexts.ordering.domain.value_objects import OrderLine, Quantity
from app.contexts.ordering.infrastructure.persistence.order_repository import (
    SqlAlchemyOrderRepository,
)
from app.shared.infrastructure.database.session_strategy import OwnSessionFactory
from tests.factories import make_ordered_book_snapshot


@pytest.fixture
def repository(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyOrderRepository:
    return SqlAlchemyOrderRepository(OwnSessionFactory(session_factory))


class TestSqlAlchemyOrderRepository:
    async def test_add_then_get_round_trips_the_order_and_its_lines(
        self, repository: SqlAlchemyOrderRepository
    ) -> None:
        order = Order.place(
            lines=[
                OrderLine(
                    snapshot=make_ordered_book_snapshot(
                        title="Domain-Driven Design", unit_price_cents=4999
                    ),
                    quantity=Quantity(2),
                ),
                OrderLine(
                    snapshot=make_ordered_book_snapshot(
                        title="Clean Architecture", unit_price_cents=3499
                    ),
                    quantity=Quantity(1),
                ),
            ]
        )

        await repository.add(order)
        fetched = await repository.get(order.id)

        assert fetched is not None
        assert fetched.id == order.id
        assert len(fetched.lines) == 2
        assert fetched.total_cents == order.total_cents
        titles = {line.snapshot.title for line in fetched.lines}
        assert titles == {"Domain-Driven Design", "Clean Architecture"}

    async def test_get_returns_none_for_an_unknown_id(
        self, repository: SqlAlchemyOrderRepository
    ) -> None:
        assert await repository.get(OrderId.new()) is None
