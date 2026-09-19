"""Asserts orchestration against a fake repository and a real (in-memory)
event bus, not against a database: the right aggregate method ran, the
repository ended up holding the right thing, and the event was published —
see the project plan's "prefer fakes over mocks". There's no
Unit-of-Work-level "committed" flag to assert on any more (transaction
control moved to the `get_session` FastAPI dependency, which application
tests don't exercise); what matters at this tier is repository state.
"""

import pytest
from abxbus import EventBus

from app.contexts.catalog.application.commands import RegisterBookCommand
from app.contexts.catalog.application.use_cases.register_book import RegisterBookUseCase
from app.contexts.catalog.domain.errors import DuplicateIsbnError
from app.contexts.catalog.domain.events import BookRegistered
from tests.factories import make_book, make_isbn
from tests.fakes import InMemoryBookRepository


@pytest.fixture
def books() -> InMemoryBookRepository:
    return InMemoryBookRepository()


class TestRegisterBook:
    async def test_stores_the_new_book(
        self, books: InMemoryBookRepository, event_bus: EventBus
    ) -> None:
        use_case = RegisterBookUseCase(books=books, event_bus=event_bus)

        book_id = await use_case.execute(
            RegisterBookCommand(title="Domain-Driven Design", isbn=make_isbn(1), price_cents=4999)
        )

        stored = await books.get(book_id)
        assert stored is not None
        assert str(stored.title) == "Domain-Driven Design"

    async def test_publishes_a_book_registered_event(
        self, books: InMemoryBookRepository, event_bus: EventBus, received_events: list[object]
    ) -> None:
        use_case = RegisterBookUseCase(books=books, event_bus=event_bus)

        book_id = await use_case.execute(
            RegisterBookCommand(title="Domain-Driven Design", isbn=make_isbn(3), price_cents=4999)
        )

        assert len(received_events) == 1
        event = received_events[0]
        assert isinstance(event, BookRegistered)
        assert event.book_id == book_id

    async def test_rejects_a_duplicate_isbn(
        self, books: InMemoryBookRepository, event_bus: EventBus, received_events: list[object]
    ) -> None:
        existing = make_book(isbn=make_isbn(4))
        await books.add(existing)
        use_case = RegisterBookUseCase(books=books, event_bus=event_bus)
        duplicate_command = RegisterBookCommand(
            title="Another Title", isbn=make_isbn(4), price_cents=1999
        )

        with pytest.raises(DuplicateIsbnError):
            await use_case.execute(duplicate_command)

        assert len(books.books) == 1
        assert received_events == []
