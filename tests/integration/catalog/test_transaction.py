"""The real counterpart to `tests/application/catalog/test_register_books_batch.py`'s
fake-backed atomicity tests — same behaviour, verified against actual
Postgres rather than a dict snapshot.
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.domain.book import Book
from app.contexts.catalog.domain.errors import DuplicateIsbnError
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title
from app.contexts.catalog.infrastructure.persistence.models import BookRow
from app.contexts.catalog.infrastructure.persistence.transaction import SqlAlchemyCatalogTransaction
from tests.factories import make_isbn


async def _row_count(session_factory: async_sessionmaker[AsyncSession]) -> int:
    async with session_factory() as session:
        return await session.scalar(select(func.count()).select_from(BookRow)) or 0


class TestSqlAlchemyCatalogTransaction:
    async def test_every_add_in_the_block_commits_together(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with SqlAlchemyCatalogTransaction(session_factory) as transaction:
            await transaction.books.add(
                Book.register(title=Title("Book A"), isbn=Isbn(make_isbn(50)), price=Money(999))
            )
            await transaction.books.add(
                Book.register(title=Title("Book B"), isbn=Isbn(make_isbn(51)), price=Money(999))
            )

        assert await _row_count(session_factory) == 2

    async def test_an_exception_rolls_back_every_add_in_the_block(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        with pytest.raises(ValueError, match="boom"):
            async with SqlAlchemyCatalogTransaction(session_factory) as transaction:
                await transaction.books.add(
                    Book.register(
                        title=Title("Would succeed alone"),
                        isbn=Isbn(make_isbn(52)),
                        price=Money(999),
                    )
                )
                raise ValueError("boom")

        # Not just "no row for this one add" — nothing from the block
        # committed at all.
        assert await _row_count(session_factory) == 0

    async def test_a_duplicate_isbn_within_the_block_rolls_back_the_whole_block(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        # `transaction.books` is the same `SqlAlchemyBookRepository.add()`
        # as the session-per-method case (see `book_repository.py`), just
        # bound to the transaction's session — so it flushes and translates
        # the unique-constraint violation into `DuplicateIsbnError` on the
        # *second* `add()` here, not a raw `IntegrityError`, and not only
        # at final commit.
        shared_isbn = make_isbn(53)
        with pytest.raises(DuplicateIsbnError):
            async with SqlAlchemyCatalogTransaction(session_factory) as transaction:
                await transaction.books.add(
                    Book.register(title=Title("First"), isbn=Isbn(shared_isbn), price=Money(999))
                )
                await transaction.books.add(
                    Book.register(
                        title=Title("Second, same ISBN"), isbn=Isbn(shared_isbn), price=Money(999)
                    )
                )

        assert await _row_count(session_factory) == 0
