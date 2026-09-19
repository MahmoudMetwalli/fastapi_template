"""Tests `PlaceOrderUseCase` against `FakeBookCatalog`, not a real
`catalog`. That's the point of routing the dependency through `ordering`'s
own `BookCatalog` port (`application/ports/book_catalog.py`): this suite
never imports anything from `app.contexts.catalog`, proving the use case
itself has no idea `catalog` exists. The real Anti-Corruption Layer
(`infrastructure/catalog_acl.py`) is exercised separately, against a real
database, in `tests/integration/ordering/test_catalog_acl.py`.
"""

from uuid import uuid4

import pytest
from abxbus import EventBus

from app.contexts.ordering.application.commands import PlaceOrderCommand, PlaceOrderItem
from app.contexts.ordering.application.use_cases.place_order import PlaceOrderUseCase
from app.contexts.ordering.domain.errors import BookNotFoundInCatalogError
from app.contexts.ordering.domain.events import OrderPlaced
from tests.factories import make_ordered_book_snapshot
from tests.fakes import FakeBookCatalog, InMemoryOrderRepository


@pytest.fixture
def orders() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()


@pytest.fixture
def catalog() -> FakeBookCatalog:
    return FakeBookCatalog()


class TestPlaceOrder:
    async def test_places_an_order_with_a_snapshot_of_each_book(
        self,
        orders: InMemoryOrderRepository,
        catalog: FakeBookCatalog,
        event_bus: EventBus,
        received_events: list[object],
    ) -> None:
        book = make_ordered_book_snapshot(title="Domain-Driven Design", unit_price_cents=4999)
        catalog.seed(book)
        use_case = PlaceOrderUseCase(orders=orders, catalog=catalog, event_bus=event_bus)

        order_id = await use_case.execute(
            PlaceOrderCommand(items=[PlaceOrderItem(book_id=book.book_id, quantity=2)])
        )

        stored = orders.orders[order_id.value]
        assert stored.total_cents == 9998
        assert stored.lines[0].snapshot.title == "Domain-Driven Design"
        assert len(received_events) == 1
        assert isinstance(received_events[0], OrderPlaced)
        assert received_events[0].total_cents == 9998

    async def test_raises_when_a_referenced_book_is_not_in_the_catalog(
        self,
        orders: InMemoryOrderRepository,
        catalog: FakeBookCatalog,
        event_bus: EventBus,
    ) -> None:
        use_case = PlaceOrderUseCase(orders=orders, catalog=catalog, event_bus=event_bus)

        with pytest.raises(BookNotFoundInCatalogError):
            await use_case.execute(
                PlaceOrderCommand(items=[PlaceOrderItem(book_id=uuid4(), quantity=1)])
            )

        assert orders.orders == {}

    async def test_a_later_catalog_price_change_does_not_affect_an_existing_order(
        self,
        orders: InMemoryOrderRepository,
        catalog: FakeBookCatalog,
        event_bus: EventBus,
    ) -> None:
        """The whole reason `OrderLine` stores a snapshot rather than a
        live reference — see `domain/value_objects.py::OrderedBookSnapshot`.
        """
        book = make_ordered_book_snapshot(unit_price_cents=1000)
        catalog.seed(book)
        use_case = PlaceOrderUseCase(orders=orders, catalog=catalog, event_bus=event_bus)
        order_id = await use_case.execute(
            PlaceOrderCommand(items=[PlaceOrderItem(book_id=book.book_id, quantity=1)])
        )

        catalog.seed(make_ordered_book_snapshot(book_id=book.book_id, unit_price_cents=2000))

        stored = orders.orders[order_id.value]
        assert stored.total_cents == 1000
