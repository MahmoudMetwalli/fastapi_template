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

`@abstractmethod` on `books` too, not just the two dunder methods — see
`application/ports/book_repository.py`'s docstring for why every port in
this template does this. One consequence worth knowing:
`SqlAlchemyCatalogTransaction.books` (and its test fake) must be a real
`@property`, not a plain instance attribute set in `__aenter__` — verified
empirically that `ABCMeta` computes abstractness from the *class*, before
any instance exists, so a same-named instance attribute doesn't satisfy an
abstract property and the class would refuse to instantiate at all.
"""

from abc import abstractmethod
from types import TracebackType
from typing import Protocol, Self

from app.contexts.catalog.application.ports.book_repository import BookRepository


class CatalogTransaction(Protocol):
    @property
    @abstractmethod
    def books(self) -> BookRepository: ...

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
