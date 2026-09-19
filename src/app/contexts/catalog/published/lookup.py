"""`CatalogLookup` is catalog's Open Host Service: the one, explicit,
stable interface other bounded contexts are allowed to depend on. It
returns the Published Language declared in `published/dtos.py`, never a
domain aggregate, a read model, or an ORM row.

`published/` sits beside `domain/`, `application/`, `infrastructure/`, and
`presentation/` as its own top-level layer within `catalog` specifically
so the boundary is easy to enforce mechanically: the
"Ordering may only depend on catalog's published interface" import-linter
contract in pyproject.toml forbids `app.contexts.ordering` from importing
`catalog.domain`, `catalog.application`, `catalog.infrastructure`, or
`catalog.presentation` — `catalog.published` is the one name deliberately
left off that list. Nothing inside `catalog` itself is expected to import
this package; it exists for consumers on the other side of the context
boundary.

A `Protocol`, like every other port in this template (see
`application/ports/book_repository.py`) — its implementation
(`infrastructure/persistence/catalog_lookup.py`) is never an explicit
subclass.
"""

from typing import Protocol
from uuid import UUID

from app.contexts.catalog.published.dtos import CatalogBookSummary


class CatalogLookup(Protocol):
    async def find_book_summary(self, book_id: UUID) -> CatalogBookSummary | None: ...
