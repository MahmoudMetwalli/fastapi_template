from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.contexts.catalog.application.read_models import BookReadModel, BookSummaryReadModel
from app.shared.application.messages import Query


@dataclass(frozen=True, slots=True, kw_only=True)
class GetBookQuery(Query[BookReadModel]):
    book_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ListBooksQuery(Query[Sequence[BookSummaryReadModel]]):
    limit: int = 20
    offset: int = 0
    title_contains: str | None = None
