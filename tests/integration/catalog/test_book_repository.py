"""Against real Postgres, not SQLite — this tier exists specifically to
catch what unit/application tests cannot: mapper round-trips, the unique-
index-to-`DuplicateIsbnError` translation, and `apply_to_row` emitting an UPDATE
rather than a second INSERT.
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.domain.errors import DuplicateIsbnError
from app.contexts.catalog.domain.value_objects import Money
from app.contexts.catalog.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from app.contexts.catalog.infrastructure.persistence.models import BookRow
from app.shared.infrastructure.database.session_strategy import OwnSessionFactory
from tests.factories import make_book, make_isbn


@pytest.fixture
def repository(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyBookRepository:
    return SqlAlchemyBookRepository(OwnSessionFactory(session_factory))


class TestSqlAlchemyBookRepository:
    async def test_add_then_get_round_trips_the_aggregate(
        self, repository: SqlAlchemyBookRepository
    ) -> None:
        book = make_book(title="Domain-Driven Design", isbn=make_isbn(10), price_cents=4999)

        await repository.add(book)
        fetched = await repository.get(book.id)

        assert fetched is not None
        assert fetched.id == book.id
        assert str(fetched.title) == "Domain-Driven Design"
        assert str(fetched.isbn) == make_isbn(10)
        assert fetched.price.amount_cents == 4999

    async def test_get_by_isbn(self, repository: SqlAlchemyBookRepository) -> None:
        book = make_book(isbn=make_isbn(11))
        await repository.add(book)

        fetched = await repository.get_by_isbn(make_isbn(11))

        assert fetched is not None
        assert fetched.id == book.id

    async def test_get_returns_none_for_an_unknown_id(
        self, repository: SqlAlchemyBookRepository
    ) -> None:
        assert await repository.get(make_book().id) is None

    async def test_adding_a_duplicate_isbn_raises_duplicate_isbn(
        self, repository: SqlAlchemyBookRepository
    ) -> None:
        isbn = make_isbn(12)
        await repository.add(make_book(isbn=isbn))
        second_book_with_same_isbn = make_book(title="A different title", isbn=isbn)

        with pytest.raises(DuplicateIsbnError):
            await repository.add(second_book_with_same_isbn)

    async def test_save_updates_the_existing_row_rather_than_inserting_a_second_one(
        self,
        repository: SqlAlchemyBookRepository,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        book = make_book(isbn=make_isbn(13), price_cents=4999)
        await repository.add(book)

        book.change_price(Money(3999))
        await repository.save(book)

        async with session_factory() as session:
            row_count = await session.scalar(
                select(func.count()).select_from(BookRow).where(BookRow.id == book.id.value)
            )
        assert row_count == 1

        fetched = await repository.get(book.id)
        assert fetched is not None
        assert fetched.price.amount_cents == 3999
