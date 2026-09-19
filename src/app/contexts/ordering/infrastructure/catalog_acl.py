"""The Anti-Corruption Layer between `ordering` and `catalog`.

This is the *only* module in `app.contexts.ordering` that imports anything
from `app.contexts.catalog` — specifically, only `catalog.published`, the
one interface `catalog` explicitly exposes to other contexts (see
`catalog/published/lookup.py`). The import-linter contract
"Ordering may only depend on catalog's published interface" in
pyproject.toml makes that mechanical rather than a rule someone has to
remember.

Its whole job is translation: it receives `catalog`'s vocabulary
(`CatalogBookSummary`) and returns `ordering`'s own
(`OrderedBookSnapshot`), so that everything upstream of this class —
`PlaceOrderUseCase`, `Order`, `OrderLine` — only ever speaks `ordering`'s
ubiquitous language and would keep working unchanged even if `catalog`
were replaced by a different implementation, a different context
entirely, or a real HTTP call to a separate service one day. That
substitutability is the point of an ACL: without one, `catalog`'s model
leaks into `ordering`'s domain the moment it's more convenient to reuse
`CatalogBookSummary` (or `catalog`'s `Book` aggregate) directly instead of
maintaining `OrderedBookSnapshot`.

See `docs/ddd-concepts.md` for the concept this class and
`ports/book_catalog.py` demonstrate together.
"""

from typing import TYPE_CHECKING
from uuid import UUID

from app.contexts.catalog.published.lookup import CatalogLookup
from app.contexts.ordering.application.ports.book_catalog import BookCatalog
from app.contexts.ordering.domain.value_objects import OrderedBookSnapshot


class CatalogAntiCorruptionLayer:
    def __init__(self, catalog_lookup: CatalogLookup) -> None:
        self._catalog_lookup = catalog_lookup

    async def find(self, book_id: UUID) -> OrderedBookSnapshot | None:
        summary = await self._catalog_lookup.find_book_summary(book_id)
        if summary is None:
            return None
        return OrderedBookSnapshot(
            book_id=summary.id,
            title=summary.title,
            unit_price_cents=summary.price_cents,
        )


if TYPE_CHECKING:
    _conforms_to_book_catalog: type[BookCatalog] = CatalogAntiCorruptionLayer
