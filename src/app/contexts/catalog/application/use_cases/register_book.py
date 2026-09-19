"""One file per use case, verb-first — not `fastapi-ddd-example`'s camelCase
`usecase/newBook/{api,command,impl}.py` (a 4-file folder per use case), and
not `fastapi-todo-ddd`'s single-`__call__` convention. A use case is a class
with an `execute()` method; no base class required.

Takes `books: BookRepository` directly, not a Unit-of-Work factory: the
transaction boundary is the whole request, owned by the
`get_session` FastAPI dependency (see
`shared/infrastructure/database/session.py`) — commits on a clean return
from the route, rolls back if this method raises. There is nothing left
for a dedicated UoW object to coordinate once only one repository is
involved.
"""

from abxbus import EventBus

from app.contexts.catalog.application.commands import RegisterBookCommand
from app.contexts.catalog.application.ports.book_repository import BookRepository
from app.contexts.catalog.domain.book import Book, BookId
from app.contexts.catalog.domain.errors import DuplicateIsbnError
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title
from app.shared.infrastructure.events import publish


class RegisterBookUseCase:
    def __init__(self, books: BookRepository, event_bus: EventBus) -> None:
        self._books = books
        self._event_bus = event_bus

    async def execute(self, command: RegisterBookCommand) -> BookId:
        isbn = Isbn(command.isbn)
        if await self._books.get_by_isbn(str(isbn)) is not None:
            raise DuplicateIsbnError(str(isbn))

        book = Book.register(
            title=Title(command.title),
            isbn=isbn,
            price=Money(command.price_cents),
        )
        await self._books.add(book)

        # Events are published immediately here, before the request's
        # transaction actually commits (that happens when the route
        # returns and `get_session`'s `async with` block exits). A
        # subscriber could in principle observe an event for a write that
        # is later rolled back by something else in the same request —
        # not a concern today, since every route calls exactly one use
        # case, but worth knowing if that ever changes. See the project
        # README's "Growing this template" for the transactional outbox
        # that removes this gap entirely.
        for event in book.pull_events():
            await publish(self._event_bus, event)

        return book.id
