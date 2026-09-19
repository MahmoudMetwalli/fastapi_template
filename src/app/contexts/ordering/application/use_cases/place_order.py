"""`PlaceOrderUseCase` is the reason this context needs to know anything
about a book at all — and it never imports `catalog`. It depends on
`BookCatalog` (`ports/book_catalog.py`), `ordering`'s own port; the
Anti-Corruption Layer bound to that port in `containers.py`
(`infrastructure/catalog_acl.py::CatalogAntiCorruptionLayer`) is the only
thing on the other side of it that has ever heard of `catalog`.

Snapshotting each line's title/price at order time (rather than storing a
live reference to a `catalog` book) is deliberate, not incidental: see
`domain/value_objects.py::OrderedBookSnapshot`.
"""

from abxbus import EventBus

from app.contexts.ordering.application.commands import PlaceOrderCommand
from app.contexts.ordering.application.ports.book_catalog import BookCatalog
from app.contexts.ordering.application.ports.order_repository import OrderRepository
from app.contexts.ordering.domain.errors import BookNotFoundInCatalogError
from app.contexts.ordering.domain.order import Order, OrderId
from app.contexts.ordering.domain.value_objects import OrderLine, Quantity
from app.shared.infrastructure.events import publish


class PlaceOrderUseCase:
    def __init__(self, orders: OrderRepository, catalog: BookCatalog, event_bus: EventBus) -> None:
        self._orders = orders
        self._catalog = catalog
        self._event_bus = event_bus

    async def execute(self, command: PlaceOrderCommand) -> OrderId:
        lines: list[OrderLine] = []
        for item in command.items:
            snapshot = await self._catalog.find(item.book_id)
            if snapshot is None:
                raise BookNotFoundInCatalogError(item.book_id)
            lines.append(OrderLine(snapshot=snapshot, quantity=Quantity(item.quantity)))

        order = Order.place(lines=lines)
        await self._orders.add(order)

        for event in order.pull_events():
            await publish(self._event_bus, event)

        return order.id
