from collections.abc import Sequence
from typing import TYPE_CHECKING

from app.contexts.catalog.application.ports.book_query_service import BookQueryService
from app.contexts.catalog.application.queries import ListBooksQuery
from app.contexts.catalog.application.read_models import BookSummaryReadModel
from app.shared.application.bus import query_handler
from app.shared.application.messages import QueryHandler


@query_handler(ListBooksQuery)
class ListBooksUseCase:
    def __init__(self, book_queries: BookQueryService) -> None:
        self._book_queries = book_queries

    async def execute(self, query: ListBooksQuery) -> Sequence[BookSummaryReadModel]:
        return await self._book_queries.list(
            limit=query.limit,
            offset=query.offset,
            title_contains=query.title_contains,
        )


if TYPE_CHECKING:
    _conforms_to_query_handler: type[
        QueryHandler[ListBooksQuery, Sequence[BookSummaryReadModel]]
    ] = ListBooksUseCase
