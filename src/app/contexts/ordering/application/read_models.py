"""Read-side output. Pydantic, like `catalog`'s `read_models.py` — flat
shapes for a screen, not carriers of invariants.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrderLineReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    book_id: UUID
    title: str
    unit_price_cents: int
    quantity: int
    subtotal_cents: int


class OrderReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    total_cents: int
    lines: list[OrderLineReadModel]
