"""Read path: goes through `book_queries`, never `books`. It never
constructs a `Book` aggregate, so it can never trigger a lazy load or run a
write-side invariant — see `ports/book_query_service.py`.
"""

from typing import TYPE_CHECKING

from app.contexts.catalog.application.ports.book_query_service import BookQueryService
from app.contexts.catalog.application.queries import GetBookQuery
from app.contexts.catalog.application.read_models import BookReadModel
from app.contexts.catalog.domain.errors import BookNotFoundError
from app.shared.application.bus import query_handler
from app.shared.application.messages import QueryHandler


@query_handler(GetBookQuery)
class GetBookUseCase:
    def __init__(self, book_queries: BookQueryService) -> None:
        self._book_queries = book_queries

    async def execute(self, query: GetBookQuery) -> BookReadModel:
        read_model = await self._book_queries.by_id(query.book_id)
        if read_model is None:
            raise BookNotFoundError(query.book_id)
        return read_model


if TYPE_CHECKING:
    _conforms_to_query_handler: type[QueryHandler[GetBookQuery, BookReadModel]] = GetBookUseCase
