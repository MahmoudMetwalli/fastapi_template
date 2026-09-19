"""The write-side port. Same shape as `catalog`'s `BookRepository` — a
`Protocol`, never explicitly subclassed by `SqlAlchemyOrderRepository` (see
`application/ports/book_repository.py` in `catalog` for why).

No `save()`: nothing in this template modifies an existing order after
it's placed. Add one the same way `catalog.BookRepository.save` exists,
when a real use case needs it — not speculatively.
"""

from typing import Protocol

from app.contexts.ordering.domain.order import Order, OrderId


class OrderRepository(Protocol):
    async def get(self, order_id: OrderId) -> Order | None: ...

    async def add(self, order: Order) -> None: ...
