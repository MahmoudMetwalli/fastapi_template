"""Implements `CatalogTransaction`. `.books` is a plain
`SqlAlchemyBookRepository` — the same class every other use case gets as a
container-managed provider — constructed here with a `BoundSession`
strategy wrapping this transaction's own session, not through the DI
container: that session is created inside `__aenter__`, at a runtime
moment no container wired at startup can reach. See
`shared/infrastructure/database/session_strategy.py` for the strategy
types and why they're safe to construct this way.
"""

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.application.ports.transaction import CatalogTransaction
from app.contexts.catalog.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from app.shared.infrastructure.database.session_strategy import BoundSession


class SqlAlchemyCatalogTransaction:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session_context: AbstractAsyncContextManager[AsyncSession] | None = None
        self.books: SqlAlchemyBookRepository

    async def __aenter__(self) -> Self:
        session_context = self._session_factory.begin()
        session = await session_context.__aenter__()
        self._session_context = session_context
        self.books = SqlAlchemyBookRepository(BoundSession(session))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session_context is not None, "__aexit__ called without a matching __aenter__"
        await self._session_context.__aexit__(exc_type, exc, tb)
        self._session_context = None


if TYPE_CHECKING:
    _conforms_to_catalog_transaction: type[CatalogTransaction] = SqlAlchemyCatalogTransaction
