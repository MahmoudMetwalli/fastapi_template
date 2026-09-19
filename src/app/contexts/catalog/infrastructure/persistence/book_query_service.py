"""The read side. Explicit column-level SELECTs, not whole-entity loads —
this is what makes it structurally impossible for a list/detail page to
trigger a lazy load or construct a `Book` aggregate just to render it.

Inherits `SqlAlchemySessionScoped` for its `SessionStrategy`, like
`SqlAlchemyBookRepository` — no query in this template currently needs to
share a transaction with anything else, but the `BoundSession` strategy is
available for free if one ever does. Explicitly subclasses `BookQueryService`
too, same reasoning as `book_repository.py`.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.contexts.catalog.application.ports.book_query_service import BookQueryService
from app.contexts.catalog.application.read_models import BookReadModel, BookSummaryReadModel
from app.contexts.catalog.infrastructure.persistence.models import BookRow
from app.shared.infrastructure.database.session_scoped import SqlAlchemySessionScoped


class SqlAlchemyBookQueryService(SqlAlchemySessionScoped, BookQueryService):
    async def by_id(self, book_id: UUID) -> BookReadModel | None:
        statement = select(BookRow.id, BookRow.title, BookRow.isbn, BookRow.price_cents).where(
            BookRow.id == book_id
        )
        async with self._strategy.session() as session:
            result = await session.execute(statement)
            row = result.mappings().one_or_none()
        return BookReadModel.model_validate(row) if row is not None else None

    async def list(
        self, *, limit: int, offset: int, title_contains: str | None = None
    ) -> Sequence[BookSummaryReadModel]:
        statement = select(BookRow.id, BookRow.title, BookRow.price_cents)
        if title_contains:
            statement = statement.where(BookRow.title.ilike(f"%{title_contains}%"))
        statement = statement.order_by(BookRow.title).limit(limit).offset(offset)

        async with self._strategy.session() as session:
            result = await session.execute(statement)
            return [BookSummaryReadModel.model_validate(row) for row in result.mappings()]
