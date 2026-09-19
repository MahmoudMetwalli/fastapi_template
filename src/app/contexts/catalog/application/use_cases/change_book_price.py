from abxbus import EventBus

from app.contexts.catalog.application.commands import ChangeBookPriceCommand
from app.contexts.catalog.application.ports.book_repository import BookRepository
from app.contexts.catalog.domain.book import BookId
from app.contexts.catalog.domain.errors import BookNotFoundError
from app.contexts.catalog.domain.value_objects import Money
from app.shared.infrastructure.events import publish


class ChangeBookPriceUseCase:
    def __init__(self, books: BookRepository, event_bus: EventBus) -> None:
        self._books = books
        self._event_bus = event_bus

    async def execute(self, command: ChangeBookPriceCommand) -> None:
        book_id = BookId(command.book_id)
        book = await self._books.get(book_id)
        if book is None:
            raise BookNotFoundError(book_id)

        book.change_price(Money(command.new_price_cents))
        await self._books.save(book)

        # See `RegisterBookUseCase.execute` for why this runs before the
        # request's actual commit, not strictly after it.
        for event in book.pull_events():
            await publish(self._event_bus, event)
