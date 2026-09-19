"""Read-side output. Pydantic, unlike the domain aggregate — these are flat,
denormalised shapes for a screen, not carriers of invariants, so Pydantic's
validation/serialization is exactly the right tool here. Deliberately not
named `BookDTO`: see the project plan's naming table for why `DTO` is
banned as a suffix in this template.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    title: str
    isbn: str
    price_cents: int


class BookSummaryReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    title: str
    price_cents: int
