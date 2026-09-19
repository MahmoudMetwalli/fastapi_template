"""Implements `catalog.published.lookup.CatalogLookup`. Lives in
`infrastructure/persistence/` alongside `book_repository.py`/
`book_query_service.py` — same pattern as every other port in this
template: the Protocol is declared where consumers can see it, the
SQLAlchemy-backed implementation lives at the infrastructure edge.

Inherits `SqlAlchemySessionScoped` like the other two persistence classes;
a `Factory` provider sharing the same `SessionStrategy` is exactly as safe
to use concurrently as `book_query_service` is, for the same reason (see
`shared/infrastructure/database/session_strategy.py`).
"""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from app.contexts.catalog.infrastructure.persistence.models import BookRow
from app.contexts.catalog.published.dtos import CatalogBookSummary
from app.contexts.catalog.published.lookup import CatalogLookup
from app.shared.infrastructure.database.session_scoped import SqlAlchemySessionScoped


class SqlAlchemyCatalogLookup(SqlAlchemySessionScoped):
    async def find_book_summary(self, book_id: UUID) -> CatalogBookSummary | None:
        statement = select(BookRow.id, BookRow.title, BookRow.price_cents).where(
            BookRow.id == book_id
        )
        async with self._strategy.session() as session:
            result = await session.execute(statement)
            row = result.mappings().one_or_none()
        # `CatalogBookSummary` is a plain dataclass, not a Pydantic model —
        # unlike `BookReadModel`/`BookSummaryReadModel`, it's not meant to
        # validate untrusted input; it's an internal-to-trusted-code data
        # carrier crossing a context boundary, so a keyword-unpack is enough.
        return CatalogBookSummary(**row) if row is not None else None


if TYPE_CHECKING:
    _conforms_to_catalog_lookup: type[CatalogLookup] = SqlAlchemyCatalogLookup
