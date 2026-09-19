"""`SqlAlchemyCatalogLookup` implements `catalog`'s published interface
(`catalog/published/lookup.py`) — this is the piece `ordering`'s Anti-
Corruption Layer depends on. See
`tests/integration/ordering/test_catalog_acl.py` for the ACL itself, tested
against this same class.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from app.contexts.catalog.infrastructure.persistence.catalog_lookup import SqlAlchemyCatalogLookup
from app.shared.infrastructure.database.session_strategy import OwnSessionFactory
from tests.factories import make_book, make_isbn


@pytest.fixture
def repository(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyBookRepository:
    return SqlAlchemyBookRepository(OwnSessionFactory(session_factory))


@pytest.fixture
def catalog_lookup(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyCatalogLookup:
    return SqlAlchemyCatalogLookup(OwnSessionFactory(session_factory))


class TestSqlAlchemyCatalogLookup:
    async def test_find_book_summary_returns_the_published_shape(
        self, repository: SqlAlchemyBookRepository, catalog_lookup: SqlAlchemyCatalogLookup
    ) -> None:
        book = make_book(title="Domain-Driven Design", isbn=make_isbn(60), price_cents=4999)
        await repository.add(book)

        summary = await catalog_lookup.find_book_summary(book.id.value)

        assert summary is not None
        assert summary.id == book.id.value
        assert summary.title == "Domain-Driven Design"
        assert summary.price_cents == 4999
        # No ISBN on the published DTO — a deliberate, smaller surface
        # than the `Book` aggregate, not an oversight. See
        # `catalog/published/dtos.py`.
        assert not hasattr(summary, "isbn")

    async def test_find_book_summary_returns_none_for_an_unknown_id(
        self, catalog_lookup: SqlAlchemyCatalogLookup
    ) -> None:
        assert await catalog_lookup.find_book_summary(make_book().id.value) is None
