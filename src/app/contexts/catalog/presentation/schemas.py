"""HTTP request/response models. Pydantic constraints live here as
`Annotated[..., StringConstraints(...)]` / `Field(gt=0)` — the Pydantic v2
replacement for v1's class-attribute style
(`class Title(ConStr): min_length = 1`), which pydantic-core no longer
reads at all. This duplicates the length/positivity bound already enforced
by the domain value objects in `Isbn`/`Title`/`Money`; that's deliberate —
it gives a fast, cheap 422 for a malformed request before any domain object
is even constructed, while the domain's `__post_init__` remains the actual
source of truth invariant.
"""

from typing import Annotated
from uuid import UUID

from pydantic import Field, StringConstraints

from app.shared.presentation.schemas import ApiModel


class RegisterBookRequest(ApiModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    isbn: str
    price_cents: Annotated[int, Field(gt=0)]


class ChangeBookPriceRequest(ApiModel):
    new_price_cents: Annotated[int, Field(gt=0)]


class BookCreatedResponse(ApiModel):
    id: UUID


class BookResponse(ApiModel):
    id: UUID
    title: str
    isbn: str
    price_cents: int


class BookSummaryResponse(ApiModel):
    id: UUID
    title: str
    price_cents: int


class BookListResponse(ApiModel):
    items: list[BookSummaryResponse]


class RegisterBookBatchItemRequest(ApiModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    isbn: str
    price_cents: Annotated[int, Field(gt=0)]


class RegisterBooksBatchRequest(ApiModel):
    items: Annotated[list[RegisterBookBatchItemRequest], Field(min_length=1)]


class BooksBatchCreatedResponse(ApiModel):
    ids: list[UUID]
