import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.infrastructure.persistence.book_query_service import (
    SqlAlchemyBookQueryService,
)
from app.contexts.catalog.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from app.shared.infrastructure.database.session_strategy import OwnSessionFactory
from tests.factories import make_book, make_isbn


@pytest.fixture
def repository(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyBookRepository:
    return SqlAlchemyBookRepository(OwnSessionFactory(session_factory))


@pytest.fixture
def query_service(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyBookQueryService:
    return SqlAlchemyBookQueryService(OwnSessionFactory(session_factory))


class TestSqlAlchemyBookQueryService:
    async def test_by_id_returns_a_read_model(
        self, repository: SqlAlchemyBookRepository, query_service: SqlAlchemyBookQueryService
    ) -> None:
        book = make_book(title="Domain-Driven Design", isbn=make_isbn(20), price_cents=4999)
        await repository.add(book)

        read_model = await query_service.by_id(book.id.value)

        assert read_model is not None
        assert read_model.id == book.id.value
        assert read_model.title == "Domain-Driven Design"
        assert read_model.price_cents == 4999

    async def test_by_id_returns_none_for_an_unknown_id(
        self, query_service: SqlAlchemyBookQueryService
    ) -> None:
        assert await query_service.by_id(make_book().id.value) is None

    async def test_list_filters_by_title_and_orders_alphabetically(
        self, repository: SqlAlchemyBookRepository, query_service: SqlAlchemyBookQueryService
    ) -> None:
        await repository.add(make_book(title="Domain-Driven Design", isbn=make_isbn(21)))
        await repository.add(make_book(title="Clean Architecture", isbn=make_isbn(22)))
        await repository.add(make_book(title="Refactoring", isbn=make_isbn(23)))

        results = await query_service.list(limit=10, offset=0)

        assert [item.title for item in results] == [
            "Clean Architecture",
            "Domain-Driven Design",
            "Refactoring",
        ]

    async def test_list_respects_limit_and_offset(
        self, repository: SqlAlchemyBookRepository, query_service: SqlAlchemyBookQueryService
    ) -> None:
        for seed in range(30, 35):
            await repository.add(make_book(title=f"Book {seed}", isbn=make_isbn(seed)))

        page = await query_service.list(limit=2, offset=1)

        assert len(page) == 2

    async def test_list_title_contains_is_case_insensitive(
        self, repository: SqlAlchemyBookRepository, query_service: SqlAlchemyBookQueryService
    ) -> None:
        await repository.add(make_book(title="Domain-Driven Design", isbn=make_isbn(40)))
        await repository.add(make_book(title="Clean Architecture", isbn=make_isbn(41)))

        results = await query_service.list(limit=10, offset=0, title_contains="domain")

        assert [item.title for item in results] == ["Domain-Driven Design"]
