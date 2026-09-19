from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class GetBookQuery:
    book_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ListBooksQuery:
    limit: int = 20
    offset: int = 0
    title_contains: str | None = None
