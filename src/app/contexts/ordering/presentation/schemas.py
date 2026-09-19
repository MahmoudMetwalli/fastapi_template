"""HTTP request/response models for `ordering`. Same conventions as
`catalog/presentation/schemas.py`.
"""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.shared.presentation.schemas import ApiModel


class PlaceOrderItemRequest(ApiModel):
    book_id: UUID
    quantity: Annotated[int, Field(gt=0)]


class PlaceOrderRequest(ApiModel):
    items: Annotated[list[PlaceOrderItemRequest], Field(min_length=1)]


class OrderCreatedResponse(ApiModel):
    id: UUID


class OrderLineResponse(ApiModel):
    book_id: UUID
    title: str
    unit_price_cents: int
    quantity: int
    subtotal_cents: int


class OrderResponse(ApiModel):
    id: UUID
    total_cents: int
    lines: list[OrderLineResponse]
