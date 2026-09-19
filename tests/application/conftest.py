"""abxbus's `EventBus` is in-memory and needs no external services, so
application tests use the real thing rather than a fake — cheaper than
writing a fake and it proves the real publish path, not a stand-in for it.
"""

from collections.abc import AsyncIterator

import pytest
from abxbus import EventBus

from app.shared.infrastructure.events import DomainEventEnvelope


@pytest.fixture
async def event_bus() -> AsyncIterator[EventBus]:
    bus = EventBus("test_events")
    try:
        yield bus
    finally:
        await bus.destroy()


@pytest.fixture
def received_events(event_bus: EventBus) -> list[object]:
    events: list[object] = []
    event_bus.on(DomainEventEnvelope, lambda envelope: events.append(envelope.event))
    return events
