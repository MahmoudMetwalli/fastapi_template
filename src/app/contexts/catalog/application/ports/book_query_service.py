"""The read-side port. Returns read models directly — an implementation is
free to issue column-level SELECTs and join across tables without ever
constructing a `Book` aggregate, which is what makes it impossible for the
read path to trigger a lazy load or run a write-side invariant.

`@abstractmethod` + explicit inheritance by every implementation — see
`application/ports/book_repository.py`'s docstring for why.
"""

from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.contexts.catalog.application.read_models import BookReadModel, BookSummaryReadModel


class BookQueryService(Protocol):
    @abstractmethod
    async def by_id(self, book_id: UUID) -> BookReadModel | None: ...

    @abstractmethod
    async def list(
        self, *, limit: int, offset: int, title_contains: str | None = None
    ) -> Sequence[BookSummaryReadModel]: ...
