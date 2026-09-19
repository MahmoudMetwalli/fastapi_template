"""Base classes for aggregates and entities.

Plain stdlib dataclasses, not Pydantic models. Pydantic is a validation and
serialization library and belongs at the edges (HTTP schemas, settings); in
the domain it adds a third-party dependency to the one layer that should
have none, and its `.model_dump()` escape hatch invites exactly the kind of
shortcut that collapses the domain/persistence boundary
(`BookRow(**book.model_dump())`).

Identity equality (not field equality) is the point of an entity, so
`eq=False` here and `__eq__`/`__hash__` are defined explicitly against `id`.
"""

from dataclasses import dataclass, field

from app.shared.domain.events import DomainEvent
from app.shared.domain.identifier import EntityId


@dataclass(slots=True, eq=False, kw_only=True)
class AggregateRoot:
    """Base class for aggregate roots.

    Subclasses declare their own `id: SomeEntityId` field; this base only
    supplies identity-based equality/hash and the event-recording seam
    (see `app/shared/domain/events.py`).
    """

    id: EntityId
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return and clear the events recorded so far. Called by the Unit
        of Work after a successful commit — never by application code
        directly, so events are only ever "published" once persistence of
        the state that produced them has actually succeeded."""
        events, self._events = self._events, []
        return events

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AggregateRoot):
            return NotImplemented
        return type(self) is type(other) and self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
