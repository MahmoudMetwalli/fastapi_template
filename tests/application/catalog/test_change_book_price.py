import pytest
from abxbus import EventBus

from app.contexts.catalog.application.commands import ChangeBookPriceCommand
from app.contexts.catalog.application.use_cases.change_book_price import ChangeBookPriceUseCase
from app.contexts.catalog.domain.errors import BookNotFoundError
from app.contexts.catalog.domain.events import BookPriceChanged
from tests.factories import make_book
from tests.fakes import InMemoryBookRepository


@pytest.fixture
def books() -> InMemoryBookRepository:
    return InMemoryBookRepository()


class TestChangeBookPrice:
    async def test_updates_the_price(
        self, books: InMemoryBookRepository, event_bus: EventBus
    ) -> None:
        book = make_book(price_cents=4999)
        await books.add(book)
        use_case = ChangeBookPriceUseCase(books=books, event_bus=event_bus)

        await use_case.execute(ChangeBookPriceCommand(book_id=book.id.value, new_price_cents=3999))

        updated = await books.get(book.id)
        assert updated is not None
        assert updated.price.amount_cents == 3999

    async def test_publishes_a_price_changed_event(
        self, books: InMemoryBookRepository, event_bus: EventBus, received_events: list[object]
    ) -> None:
        book = make_book(price_cents=4999)
        await books.add(book)
        use_case = ChangeBookPriceUseCase(books=books, event_bus=event_bus)

        await use_case.execute(ChangeBookPriceCommand(book_id=book.id.value, new_price_cents=3999))

        assert len(received_events) == 1
        event = received_events[0]
        assert isinstance(event, BookPriceChanged)
        assert event.old_amount_cents == 4999
        assert event.new_amount_cents == 3999

    async def test_raises_when_the_book_does_not_exist(
        self, books: InMemoryBookRepository, event_bus: EventBus, received_events: list[object]
    ) -> None:
        use_case = ChangeBookPriceUseCase(books=books, event_bus=event_bus)
        command = ChangeBookPriceCommand(book_id=make_book().id.value, new_price_cents=3999)

        with pytest.raises(BookNotFoundError):
            await use_case.execute(command)

        assert received_events == []
