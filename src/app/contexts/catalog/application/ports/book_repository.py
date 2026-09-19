"""The write-side port. Returns/accepts `Book` aggregates — never rows,
never read models. A `Protocol` with `@abstractmethod` members, explicitly
subclassed by `SqlAlchemyBookRepository` and every test fake — verified
empirically that this combination (not a purely structural Protocol) is
what makes conformance an enforced fact rather than a hoped-for one: a
wrong signature on an override is a `mypy` error at the implementation's
own definition, and a forgotten override raises `TypeError` the moment
anything constructs the class. See `docs/ddd-concepts.md`'s "Anti-
Corruption Layer" neighbor sections, and `shared/application/messages.py`
for the same pattern applied to command/query handlers.
"""

from abc import abstractmethod
from typing import Protocol

from app.contexts.catalog.domain.book import Book, BookId


class BookRepository(Protocol):
    @abstractmethod
    async def get(self, book_id: BookId) -> Book | None: ...

    @abstractmethod
    async def get_by_isbn(self, isbn: str) -> Book | None: ...

    @abstractmethod
    async def add(self, book: Book) -> None: ...

    @abstractmethod
    async def save(self, book: Book) -> None: ...
