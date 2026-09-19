from dataclasses import dataclass

from app.shared.domain.events import DomainEvent
from app.shared.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderPlaced(DomainEvent):
    order_id: EntityId
    total_cents: int
