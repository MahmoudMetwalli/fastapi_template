"""`SqlAlchemyBookRepository` inherits its `SessionStrategy` from
`SqlAlchemySessionScoped` (`shared/infrastructure/database/`) — the
default strategy (`OwnSessionFactory`) opens and closes a fresh session per
method call, so it carries no per-request state and can be a plain,
container-managed provider (see `containers.py`). The other strategy
(`BoundSession`) reuses one already-open session for every call, used only
by `SqlAlchemyCatalogTransaction` (`transaction.py`), for the one use case
(`RegisterBooksBatchUseCase`) that needs several `add()` calls to commit or
roll back as a single atomic unit — something the default strategy cannot
provide, since each call would be its own transaction.
"""

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.contexts.catalog.application.ports.book_repository import BookRepository
from app.contexts.catalog.domain.book import Book, BookId
from app.contexts.catalog.domain.errors import BookNotFoundError, DuplicateIsbnError
from app.contexts.catalog.infrastructure.persistence.mappers import apply_to_row, to_domain, to_row
from app.contexts.catalog.infrastructure.persistence.models import BookRow
from app.shared.infrastructure.database.session_scoped import SqlAlchemySessionScoped


class SqlAlchemyBookRepository(SqlAlchemySessionScoped):
    async def get(self, book_id: BookId) -> Book | None:
        async with self._strategy.session() as session:
            row = await session.get(BookRow, book_id.value)
            return to_domain(row) if row is not None else None

    async def get_by_isbn(self, isbn: str) -> Book | None:
        async with self._strategy.session() as session:
            result = await session.execute(select(BookRow).where(BookRow.isbn == isbn))
            row = result.scalar_one_or_none()
            return to_domain(row) if row is not None else None

    async def add(self, book: Book) -> None:
        async with self._strategy.session() as session:
            session.add(to_row(book))
            try:
                # `autoflush=False` (see `containers.py`), so without an
                # explicit flush here the INSERT wouldn't run until the
                # transaction commits — too late to translate a
                # unique-constraint violation into `DuplicateIsbnError` at
                # a point the use case can still react to it. Defense in
                # depth against the TOCTOU race in `RegisterBookUseCase`
                # (which checks `get_by_isbn` before calling `add`, but two
                # concurrent requests can both pass that check).
                await session.flush()
            except IntegrityError as exc:
                # No explicit `session.rollback()` needed: re-raising here
                # lets it propagate out of the `async with` block above,
                # whose own `__aexit__` rolls back on any exception.
                raise DuplicateIsbnError(str(book.isbn)) from exc

    async def save(self, book: Book) -> None:
        async with self._strategy.session() as session:
            # `session.get` on an already-loaded row is served from the
            # identity map, so this is usually not a round trip.
            row = await session.get(BookRow, book.id.value)
            if row is None:
                raise BookNotFoundError(book.id)
            apply_to_row(book, row)


if TYPE_CHECKING:
    # Closes the mypy use-site gap documented in the project plan: this
    # class is never explicitly subclassed from `BookRepository` (see
    # "Ports: Protocol or ABC?"), so without this line a signature mismatch
    # between the two would go unnoticed until something actually tries to
    # use it as a `BookRepository`.
    _conforms_to_book_repository: type[BookRepository] = SqlAlchemyBookRepository
