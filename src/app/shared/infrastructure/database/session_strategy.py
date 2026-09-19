"""The two ways any repository/query-service in this template can get an
`AsyncSession`, as a formal Strategy (GoF sense) rather than an `isinstance`
check: each implementation is immutable once constructed — no setter, no
way to swap it after the fact — which is what keeps it safe to share a
single `SqlAlchemyBookRepository` instance across concurrent requests (see
`containers.py`): nothing on `self` ever changes between calls, so there is
nothing for one request to race with another over.

- `OwnSessionFactory` — the default. Opens and closes a fresh session per
  call.
- `BoundSession` — reuses one already-open session for every call. Used
  only by `SqlAlchemyCatalogTransaction` (`contexts/catalog/infrastructure/
  persistence/transaction.py`), constructed directly with the session that
  transaction just opened — not through the DI container, since that
  session is born at runtime, inside one `async with` block, at a moment
  no container wired at startup can reach. See that module's docstring.
"""

from contextlib import AbstractAsyncContextManager, nullcontext
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionStrategy(Protocol):
    def session(self) -> AbstractAsyncContextManager[AsyncSession]: ...


class OwnSessionFactory:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    def session(self) -> AbstractAsyncContextManager[AsyncSession]:
        return self._session_factory.begin()


class BoundSession:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def session(self) -> AbstractAsyncContextManager[AsyncSession]:
        # No commit/close here — the transaction that owns this session
        # manages its whole lifecycle; this strategy just hands the same
        # session back on every call.
        return nullcontext(self._session)
