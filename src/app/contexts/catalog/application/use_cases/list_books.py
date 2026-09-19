from collections.abc import Sequence

from app.contexts.catalog.application.ports.book_query_service import BookQueryService
from app.contexts.catalog.application.queries import ListBooksQuery
from app.contexts.catalog.application.read_models import BookSummaryReadModel
from app.shared.application.bus import query_handler
from app.shared.application.messages import QueryHandler


@query_handler(ListBooksQuery)
class ListBooksUseCase(QueryHandler[ListBooksQuery, Sequence[BookSummaryReadModel]]):
    def __init__(self, book_queries: BookQueryService) -> None:
        self._book_queries = book_queries

    async def execute(self, query: ListBooksQuery) -> Sequence[BookSummaryReadModel]:
        return await self._book_queries.list(
            limit=query.limit,
            offset=query.offset,
            title_contains=query.title_contains,
        )
