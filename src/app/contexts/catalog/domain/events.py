from dataclasses import dataclass

from app.shared.domain.events import DomainEvent
from app.shared.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, kw_only=True)
class BookRegistered(DomainEvent):
    book_id: EntityId
    isbn: str


@dataclass(frozen=True, slots=True, kw_only=True)
class BookPriceChanged(DomainEvent):
    book_id: EntityId
    old_amount_cents: int
    new_amount_cents: int
