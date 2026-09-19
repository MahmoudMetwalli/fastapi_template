"""The one use case in this template that needs `CatalogTransaction`
rather than a plain `BookRepository` — importing a batch of books where a
single invalid or duplicate entry must roll back the *whole* batch, not
leave a partial import behind. Every other use case here takes
`BookRepository`/`BookQueryService` directly; see the port's docstring for
why this one is different.

Takes an already-built `CatalogTransaction`, not a factory the use case
calls itself — one `execute()` call needs exactly one transaction for the
whole batch, and `providers.Factory` in `containers.py` already builds a
fresh one every time this use case itself is resolved (once per request),
so there's nothing left for a stored "call me again" callable to provide.
An earlier version injected `catalog_transaction.provider` for the use
case to call directly; that went through dependency-injector's own
resolution machinery on every call, which could return the transaction or
an awaitable of it depending on internal caching state — verified the hard
way. Injecting the resolved object directly removes that ambiguity
entirely rather than working around it.
"""

from abxbus import EventBus

from app.contexts.catalog.application.commands import RegisterBooksBatchCommand
from app.contexts.catalog.application.ports.transaction import CatalogTransaction
from app.contexts.catalog.domain.book import Book, BookId
from app.contexts.catalog.domain.errors import DuplicateIsbnError
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title
from app.shared.infrastructure.events import publish


class RegisterBooksBatchUseCase:
    def __init__(self, transaction: CatalogTransaction, event_bus: EventBus) -> None:
        self._transaction = transaction
        self._event_bus = event_bus

    async def execute(self, command: RegisterBooksBatchCommand) -> list[BookId]:
        books: list[Book] = []
        async with self._transaction as transaction:
            for item in command.items:
                isbn = Isbn(item.isbn)
                if await transaction.books.get_by_isbn(str(isbn)) is not None:
                    # Raising here exits the `async with` block via an
                    # exception, rolling back every `add()` already done
                    # for earlier items in this same batch — not just this
                    # one entry.
                    raise DuplicateIsbnError(str(isbn))

                book = Book.register(
                    title=Title(item.title), isbn=isbn, price=Money(item.price_cents)
                )
                await transaction.books.add(book)
                books.append(book)

        # Only reached once the whole batch has committed.
        for book in books:
            for event in book.pull_events():
                await publish(self._event_bus, event)

        return [book.id for book in books]
