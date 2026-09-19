"""Proves the Anti-Corruption Layer's translation end-to-end against real
data: a book registered through `catalog`'s own repository is found, and
correctly translated into `ordering`'s vocabulary, by
`CatalogAntiCorruptionLayer` wrapping a real `SqlAlchemyCatalogLookup` — no
fakes on either side of the context boundary this time. Compare
`tests/application/ordering/test_place_order.py`, which fakes this whole
port to test `PlaceOrderUseCase` in isolation from both `catalog` and a
database.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from app.contexts.catalog.infrastructure.persistence.catalog_lookup import SqlAlchemyCatalogLookup
from app.contexts.ordering.infrastructure.catalog_acl import CatalogAntiCorruptionLayer
from app.shared.infrastructure.database.session_strategy import OwnSessionFactory
from tests.factories import make_book, make_isbn


@pytest.fixture
def repository(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyBookRepository:
    return SqlAlchemyBookRepository(OwnSessionFactory(session_factory))


@pytest.fixture
def acl(session_factory: async_sessionmaker[AsyncSession]) -> CatalogAntiCorruptionLayer:
    catalog_lookup = SqlAlchemyCatalogLookup(OwnSessionFactory(session_factory))
    return CatalogAntiCorruptionLayer(catalog_lookup)


class TestCatalogAntiCorruptionLayer:
    async def test_translates_a_real_catalog_book_into_an_ordered_book_snapshot(
        self, repository: SqlAlchemyBookRepository, acl: CatalogAntiCorruptionLayer
    ) -> None:
        book = make_book(title="Refactoring", isbn=make_isbn(61), price_cents=3499)
        await repository.add(book)

        snapshot = await acl.find(book.id.value)

        assert snapshot is not None
        assert snapshot.book_id == book.id.value
        assert snapshot.title == "Refactoring"
        assert snapshot.unit_price_cents == 3499

    async def test_returns_none_for_a_book_that_does_not_exist(
        self, acl: CatalogAntiCorruptionLayer
    ) -> None:
        assert await acl.find(make_book().id.value) is None
