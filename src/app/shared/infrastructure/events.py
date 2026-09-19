"""The event bus boundary. Domain events stay plain, dependency-free
dataclasses (`shared/domain/events.py`) — abxbus is used only here, at the
infrastructure edge, as the dispatch mechanism. Nothing in `domain/` or
`application/ports/` imports abxbus or pydantic.

Use cases pull events off an aggregate and call `publish()` for each one
themselves (see `RegisterBookUseCase.execute`) — there is no dedicated
object draining them automatically. This is in-memory and best-effort: it
runs before the request's actual transaction commits (that happens later,
in `get_session`'s cleanup), so a subscriber could in principle observe an
event for a write that a later failure in the same request rolls back.
That is an accepted v1 tradeoff, not a hidden one — see the project
README's "Growing this template" section for the transactional outbox
that would close this gap.
"""

from typing import Any

from abxbus import BaseEvent, EventBus
from dependency_injector import resources
from pydantic import ConfigDict

from app.shared.domain.events import DomainEvent


class DomainEventEnvelope(BaseEvent):  # type: ignore[misc]
    """A generic abxbus envelope around any `DomainEvent`. abxbus routes
    and validates via Pydantic, and `BaseEvent` cannot be made generic over
    a stdlib dataclass without colliding with its own type parameter
    (verified empirically) — so this carries the event as `Any` rather
    than needing one abxbus subclass per domain event type. A handler that
    wants only `BookRegistered` events does its own `isinstance` check on
    `envelope.event`.

    The `type: ignore[misc]` is `disallow_subclassing_any` (part of
    `strict`): abxbus ships no `py.typed` marker, so `BaseEvent` resolves
    to `Any` under mypy and subclassing it is flagged. This is the one
    place in the codebase that subclass happens, by design.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    event: Any


async def publish(bus: EventBus, event: DomainEvent) -> None:
    await bus.emit(DomainEventEnvelope(event=event)).now()


class EventBusResource(resources.AsyncResource[EventBus]):
    """A `dependency_injector.resources.AsyncResource` subclass, not a bare
    async-generator function — this is the library's own idiom for a
    resource with init/shutdown, and it's what `containers.py`'s
    `providers.Resource(EventBusResource)` expects: `init()` builds the
    resource, `shutdown()` tears it down. Note `init`/`shutdown`, not
    `__init__` — `AsyncResource.__init__` is already defined by the base
    class to store constructor args/kwargs for `init()` to receive.
    """

    async def init(self) -> EventBus:
        return EventBus("domain_events")

    async def shutdown(self, resource: EventBus | None) -> None:
        if resource is not None:
            await resource.destroy()
