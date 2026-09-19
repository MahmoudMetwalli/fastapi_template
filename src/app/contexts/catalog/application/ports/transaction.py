"""A port for the one use case in this template that needs several
repository calls to commit — or roll back — as a single atomic unit:
importing a batch of books, where one invalid or duplicate entry must undo
the whole batch, not leave a partial import behind.

Every other use case here (`RegisterBookUseCase`, `GetBookUseCase`, ...)
takes `BookRepository`/`BookQueryService` directly, each managing its own
session per call (see `infrastructure/persistence/book_repository.py`).
That can't satisfy "all N writes commit together or none do," so this
exists — deliberately scoped to exactly the one use case that needs it,
not reintroduced as a generic per-request Unit of Work. See the project
README for why the generic version was removed, and
`RegisterBooksBatchUseCase` for the one case where a purpose-built,
narrowly-scoped version of the same shape earns its keep back.

Shaped to generalize past one repository, not just past one call: exposes
every repository this *context* has, all bound to the same transaction —
today just `books`, but if `catalog` ever grows a second aggregate (and
its own repository), that repository joins this same port. That's the
answer to "what about atomicity across multiple repositories" for a
context that, so far, only has one.
"""

from types import TracebackType
from typing import Protocol, Self

from app.contexts.catalog.application.ports.book_repository import BookRepository


class CatalogTransaction(Protocol):
    @property
    def books(self) -> BookRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
