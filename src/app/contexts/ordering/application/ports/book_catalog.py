"""`BookCatalog` is `ordering`'s *own* port for "I need to know about a
book to place an order" — note the return type is `OrderedBookSnapshot`,
`ordering`'s own value object, never `catalog`'s `CatalogBookSummary` or
`Book`.

This port is the seam an Anti-Corruption Layer plugs into. Its
implementation, `infrastructure/catalog_acl.py::CatalogAntiCorruptionLayer`,
is the *only* place in `app.contexts.ordering` allowed to know `catalog`
exists — everything upstream of this port (`PlaceOrderUseCase`, `Order`,
`OrderLine`) only ever speaks `ordering`'s own ubiquitous language. A test
double for this port (`tests/fakes.py::FakeBookCatalog`) needs no
knowledge of `catalog` either, for the same reason.

`None` means "no such book" — deciding whether that's an error is the
calling use case's job, not this port's; see `domain/errors.py
::BookNotFoundInCatalogError`.
"""

from typing import Protocol
from uuid import UUID

from app.contexts.ordering.domain.value_objects import OrderedBookSnapshot


class BookCatalog(Protocol):
    async def find(self, book_id: UUID) -> OrderedBookSnapshot | None: ...
