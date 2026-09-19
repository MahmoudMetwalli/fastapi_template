from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class PlaceOrderItem:
    book_id: UUID
    quantity: int


@dataclass(frozen=True, slots=True, kw_only=True)
class PlaceOrderCommand:
    items: Sequence[PlaceOrderItem]
