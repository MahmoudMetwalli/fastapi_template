"""The write-side port. Same shape as `catalog`'s `BookRepository` — a
`Protocol` with `@abstractmethod` members, explicitly subclassed by
`SqlAlchemyOrderRepository` and its test fake (see
`application/ports/book_repository.py` in `catalog` for why).

No `save()`: nothing in this template modifies an existing order after
it's placed. Add one the same way `catalog.BookRepository.save` exists,
when a real use case needs it — not speculatively.
"""

from abc import abstractmethod
from typing import Protocol

from app.contexts.ordering.domain.order import Order, OrderId


class OrderRepository(Protocol):
    @abstractmethod
    async def get(self, order_id: OrderId) -> Order | None: ...

    @abstractmethod
    async def add(self, order: Order) -> None: ...
