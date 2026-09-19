"""No try/except anywhere here. `DomainError` subclasses raised by a use
case propagate straight to the handlers registered in
`shared/presentation/error_handlers.py` — contrast `fastapi-todo-ddd`, which
wraps every use case call in `except Exception: raise HTTPException(500)`,
turning every domain error into an opaque 500.

Routes depend on `CommandBus`/`QueryBus` (`shared/application/bus.py`),
not a specific use case — this router doesn't import any of
`RegisterBookUseCase`, `GetBookUseCase`, etc. at all. `bus.dispatch(...)`
still returns the real result type (`BookId`, `BookReadModel`, ...) under
mypy, not `Any` — see `application/commands.py`/`queries.py`, where each
command/query declares that type as `Command[R]`/`Query[R]`.

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
from app.shared.application.bus import CommandBus, QueryBus

router = APIRouter(prefix="/books", tags=["catalog"])

Commands = Annotated[CommandBus, Depends(Provide[Container.command_bus])]
Queries = Annotated[QueryBus, Depends(Provide[Container.query_bus])]


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def register_book(payload: RegisterBookRequest, bus: Commands) -> BookCreatedResponse:
    book_id = await bus.dispatch(
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
    payload: RegisterBooksBatchRequest, bus: Commands
) -> BooksBatchCreatedResponse:
    book_ids = await bus.dispatch(
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
async def get_book(book_id: UUID, bus: Queries) -> BookResponse:
    read_model = await bus.dispatch(GetBookQuery(book_id=book_id))
    return BookResponse.model_validate(read_model)


@router.get("")
@inject
async def list_books(
    bus: Queries,
    limit: Annotated[int, Query(gt=0, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    title_contains: str | None = None,
) -> BookListResponse:
    read_models = await bus.dispatch(
        ListBooksQuery(limit=limit, offset=offset, title_contains=title_contains)
    )
    return BookListResponse(
        items=[BookSummaryResponse.model_validate(item) for item in read_models]
    )


@router.patch("/{book_id}/price", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def change_book_price(book_id: UUID, payload: ChangeBookPriceRequest, bus: Commands) -> None:
    await bus.dispatch(
        ChangeBookPriceCommand(book_id=book_id, new_price_cents=payload.new_price_cents)
    )
