"""The write-side port. Returns/accepts `Book` aggregates — never rows,
never read models. A `Protocol`, not explicitly subclassed by
`SqlAlchemyBookRepository` (see the project plan's "Ports: Protocol or ABC?"
section) so infrastructure has no runtime dependency on the application
layer.
"""

from typing import Protocol

from app.contexts.catalog.domain.book import Book, BookId


class BookRepository(Protocol):
    async def get(self, book_id: BookId) -> Book | None: ...

    async def get_by_isbn(self, isbn: str) -> Book | None: ...

    async def add(self, book: Book) -> None: ...

    async def save(self, book: Book) -> None: ...
