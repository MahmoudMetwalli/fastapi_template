"""Implements `CatalogTransaction`. `.books` is a plain
`SqlAlchemyBookRepository` — the same class every other use case gets as a
container-managed provider — constructed here with a `BoundSession`
strategy wrapping this transaction's own session, not through the DI
container: that session is created inside `__aenter__`, at a runtime
moment no container wired at startup can reach. See
`shared/infrastructure/database/session_strategy.py` for the strategy
types and why they're safe to construct this way.

`books` is a real `@property` backed by `_books`, not a plain instance
attribute set in `__aenter__` — required, not stylistic:
`CatalogTransaction.books` is an `@abstractmethod` property, and `ABCMeta`
computes a class's abstractness from its *class-level* attributes before
any instance exists, so a same-named instance attribute doesn't satisfy
it — verified empirically (attempting to instantiate with a plain
attribute raised `TypeError: Can't instantiate abstract class ... without
an implementation for abstract method 'books'`). The property raises if
read before `__aenter__` runs, which is the only way `.books` could ever
be accessed on a transaction that was never entered.
"""

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.application.ports.transaction import CatalogTransaction
from app.contexts.catalog.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from app.shared.infrastructure.database.session_strategy import BoundSession


class SqlAlchemyCatalogTransaction(CatalogTransaction):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session_context: AbstractAsyncContextManager[AsyncSession] | None = None
        self._books: SqlAlchemyBookRepository | None = None

    @property
    def books(self) -> SqlAlchemyBookRepository:
        assert self._books is not None, "__aenter__ has not run yet"
        return self._books

    async def __aenter__(self) -> Self:
        session_context = self._session_factory.begin()
        session = await session_context.__aenter__()
        self._session_context = session_context
        self._books = SqlAlchemyBookRepository(BoundSession(session))
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
