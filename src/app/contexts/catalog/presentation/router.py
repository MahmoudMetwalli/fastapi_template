"""No try/except anywhere here. `DomainError` subclasses raised by a use
case propagate straight to the handlers registered in
`shared/presentation/error_handlers.py` — contrast `fastapi-todo-ddd`, which
wraps every use case call in `except Exception: raise HTTPException(500)`,
turning every domain error into an opaque 500.

`@inject` + `Provide[Container.x_use_case]` on every route: every
repository/query-service/use-case in `catalog` is container-managed now
(see `containers.py`) — none of them carry per-request state, so there's
no request-scoped dependency chain to plumb through plain `Depends()`.
`@inject` must be the innermost decorator (directly above `def`, below
`@router...`) — that's the most common way this integration breaks. See
the project README for why no module here uses
`from __future__ import annotations`, which is the other common way it
breaks (postponed annotations hide the `Provide[...]` marker from
`@inject`'s detection).
"""

from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.containers import Container
from app.contexts.catalog.application.commands import (
    ChangeBookPriceCommand,
    RegisterBookBatchItem,
    RegisterBookCommand,
    RegisterBooksBatchCommand,
)
from app.contexts.catalog.application.queries import GetBookQuery, ListBooksQuery
from app.contexts.catalog.application.use_cases.change_book_price import ChangeBookPriceUseCase
from app.contexts.catalog.application.use_cases.get_book import GetBookUseCase
from app.contexts.catalog.application.use_cases.list_books import ListBooksUseCase
from app.contexts.catalog.application.use_cases.register_book import RegisterBookUseCase
from app.contexts.catalog.application.use_cases.register_books_batch import (
    RegisterBooksBatchUseCase,
)
from app.contexts.catalog.presentation.schemas import (
    BookCreatedResponse,
    BookListResponse,
    BookResponse,
    BooksBatchCreatedResponse,
    BookSummaryResponse,
    ChangeBookPriceRequest,
    RegisterBookRequest,
    RegisterBooksBatchRequest,
)

router = APIRouter(prefix="/books", tags=["catalog"])

RegisterBookUC = Annotated[RegisterBookUseCase, Depends(Provide[Container.register_book_use_case])]
ChangeBookPriceUC = Annotated[
    ChangeBookPriceUseCase, Depends(Provide[Container.change_book_price_use_case])
]
GetBookUC = Annotated[GetBookUseCase, Depends(Provide[Container.get_book_use_case])]
ListBooksUC = Annotated[ListBooksUseCase, Depends(Provide[Container.list_books_use_case])]
RegisterBooksBatchUC = Annotated[
    RegisterBooksBatchUseCase, Depends(Provide[Container.register_books_batch_use_case])
]


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def register_book(
    payload: RegisterBookRequest, use_case: RegisterBookUC
) -> BookCreatedResponse:
    book_id = await use_case.execute(
        RegisterBookCommand(
            title=payload.title,
            isbn=payload.isbn,
            price_cents=payload.price_cents,
        )
    )
    return BookCreatedResponse(id=book_id.value)


@router.post("/batch", status_code=status.HTTP_201_CREATED)
@inject
async def register_books_batch(
    payload: RegisterBooksBatchRequest, use_case: RegisterBooksBatchUC
) -> BooksBatchCreatedResponse:
    book_ids = await use_case.execute(
        RegisterBooksBatchCommand(
            items=[
                RegisterBookBatchItem(
                    title=item.title, isbn=item.isbn, price_cents=item.price_cents
                )
                for item in payload.items
            ]
        )
    )
    return BooksBatchCreatedResponse(ids=[book_id.value for book_id in book_ids])


@router.get("/{book_id}")
@inject
async def get_book(book_id: UUID, use_case: GetBookUC) -> BookResponse:
    read_model = await use_case.execute(GetBookQuery(book_id=book_id))
    return BookResponse.model_validate(read_model)


@router.get("")
@inject
async def list_books(
    use_case: ListBooksUC,
    limit: Annotated[int, Query(gt=0, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    title_contains: str | None = None,
) -> BookListResponse:
    read_models = await use_case.execute(
        ListBooksQuery(limit=limit, offset=offset, title_contains=title_contains)
    )
    return BookListResponse(
        items=[BookSummaryResponse.model_validate(item) for item in read_models]
    )


@router.patch("/{book_id}/price", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def change_book_price(
    book_id: UUID, payload: ChangeBookPriceRequest, use_case: ChangeBookPriceUC
) -> None:
    await use_case.execute(
        ChangeBookPriceCommand(book_id=book_id, new_price_cents=payload.new_price_cents)
    )
