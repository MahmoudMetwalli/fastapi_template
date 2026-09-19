"""Read path: goes through `book_queries`, never `books`. It never
constructs a `Book` aggregate, so it can never trigger a lazy load or run a
write-side invariant — see `ports/book_query_service.py`.
"""

from app.contexts.catalog.application.ports.book_query_service import BookQueryService
from app.contexts.catalog.application.queries import GetBookQuery
from app.contexts.catalog.application.read_models import BookReadModel
from app.contexts.catalog.domain.errors import BookNotFoundError


class GetBookUseCase:
    def __init__(self, book_queries: BookQueryService) -> None:
        self._book_queries = book_queries

    async def execute(self, query: GetBookQuery) -> BookReadModel:
        read_model = await self._book_queries.by_id(query.book_id)
        if read_model is None:
            raise BookNotFoundError(query.book_id)
        return read_model
