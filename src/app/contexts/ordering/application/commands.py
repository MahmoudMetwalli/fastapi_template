from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.contexts.ordering.domain.order import OrderId
from app.shared.application.messages import Command


@dataclass(frozen=True, slots=True, kw_only=True)
class PlaceOrderItem:
    book_id: UUID
    quantity: int


@dataclass(frozen=True, slots=True, kw_only=True)
class PlaceOrderCommand(Command[OrderId]):
    items: Sequence[PlaceOrderItem]
