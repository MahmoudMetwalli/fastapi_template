"""Domain event base.

Kept a plain, dependency-free dataclass on purpose — subclasses like
`BookRegistered` must not import Pydantic, abxbus, or anything else from
`shared/infrastructure/`. Aggregates record events via
`AggregateRoot.record_event()`; a use case pulls them (via `pull_events()`)
after doing its work and publishes each one through the real event bus
(abxbus) at `shared/infrastructure/events.py::publish` — that boundary
module is where a plain dataclass event turns into something dispatchable,
and it's the only place allowed to know abxbus exists.

This is in-memory and best-effort, not a transactional outbox: no retry,
no persistence, no ordering guarantee beyond "one process, one call to
`publish()` per event." See the project README's "Growing this template"
for when an outbox (a table written in the same transaction as the
aggregate, drained by a worker) becomes worth the extra machinery.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base class for domain events. Subclasses are named in the past
    tense, e.g. `BookRegistered`, `BookPriceChanged`."""

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
