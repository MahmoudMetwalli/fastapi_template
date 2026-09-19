"""Dict-backed fakes, not `unittest.mock.AsyncMock`. A fake catches "saved
the wrong object" and read-your-writes bugs that a mock happily accepts
because it never actually stores anything — see the project plan's testing
section. Each one explicitly subclasses its port, same as every real
implementation — see `app/contexts/catalog/application/ports/
book_repository.py`'s docstring for why that's no longer purely structural
in this template.
"""

from collections.abc import Sequence
from typing import Self
from uuid import UUID

from app.contexts.catalog.application.ports.book_query_service import BookQueryService
from app.contexts.catalog.application.ports.book_repository import BookRepository
from app.contexts.catalog.application.ports.transaction import CatalogTransaction
from app.contexts.catalog.application.read_models import BookReadModel, BookSummaryReadModel
from app.contexts.catalog.domain.book import Book, BookId
from app.contexts.ordering.application.ports.book_catalog import BookCatalog
from app.contexts.ordering.application.ports.order_repository import OrderRepository
from app.contexts.ordering.domain.order import Order, OrderId
from app.contexts.ordering.domain.value_objects import OrderedBookSnapshot


class InMemoryBookRepository(BookRepository):
    def __init__(self) -> None:
        self.books: dict[UUID, Book] = {}

    async def get(self, book_id: BookId) -> Book | None:
        return self.books.get(book_id.value)

    async def get_by_isbn(self, isbn: str) -> Book | None:
        return next((book for book in self.books.values() if str(book.isbn) == isbn), None)

    async def add(self, book: Book) -> None:
        self.books[book.id.value] = book

    async def save(self, book: Book) -> None:
        self.books[book.id.value] = book


class InMemoryBookQueryService(BookQueryService):
    """Reads from the same dict an `InMemoryBookRepository` writes to,
    mirroring how the real `get_session`-scoped repository and query
    service share one session in production."""

    def __init__(self, repository: InMemoryBookRepository) -> None:
        self._repository = repository

    async def by_id(self, book_id: UUID) -> BookReadModel | None:
        book = self._repository.books.get(book_id)
        if book is None:
            return None
        return BookReadModel(
            id=book.id.value,
            title=str(book.title),
            isbn=str(book.isbn),
            price_cents=book.price.amount_cents,
        )

    async def list(
        self, *, limit: int, offset: int, title_contains: str | None = None
    ) -> Sequence[BookSummaryReadModel]:
        books = sorted(self._repository.books.values(), key=lambda book: str(book.title))
        if title_contains:
            books = [book for book in books if title_contains.lower() in str(book.title).lower()]
        page = books[offset : offset + limit]
        return [
            BookSummaryReadModel(
                id=book.id.value, title=str(book.title), price_cents=book.price.amount_cents
            )
            for book in page
        ]


class FakeCatalogTransaction(CatalogTransaction):
    """A dict-snapshot analogue of a real transaction: on a clean
    `__aexit__` the batch's writes stay (they're already in the shared
    dict); on an exception, the dict is restored to what it was before
    `__aenter__`, undoing every `add()` from this batch — including ones
    for earlier items that would have succeeded on their own. This is what
    lets an application-layer test assert the atomicity `CatalogTransaction`
    exists to provide, without a real database.

    `books` is a real `@property`, not a plain instance attribute — same
    reason as `SqlAlchemyCatalogTransaction`: `CatalogTransaction.books` is
    an `@abstractmethod` property, and a same-named instance attribute
    doesn't satisfy it (verified empirically; see that class's docstring).
    """

    def __init__(self, repository: InMemoryBookRepository) -> None:
        self._books = repository
        self._snapshot: dict[UUID, Book] | None = None

    @property
    def books(self) -> InMemoryBookRepository:
        return self._books

    async def __aenter__(self) -> Self:
        self._snapshot = dict(self._books.books)
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object
    ) -> None:
        assert self._snapshot is not None
        if exc_type is not None:
            self._books.books = self._snapshot
        self._snapshot = None


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self.orders: dict[UUID, Order] = {}

    async def get(self, order_id: OrderId) -> Order | None:
        return self.orders.get(order_id.value)

    async def add(self, order: Order) -> None:
        self.orders[order.id.value] = order


class FakeBookCatalog(BookCatalog):
    """A test double for `ordering`'s `BookCatalog` port — not for
    `catalog`'s own `CatalogLookup`. It has no idea `catalog` exists, which
    is exactly the point of the Anti-Corruption Layer this stands in for
    (`ordering/infrastructure/catalog_acl.py`): an application-layer test
    of `PlaceOrderUseCase` should never need to know, or care, what's on
    the other side of that port.
    """

    def __init__(self) -> None:
        self.books: dict[UUID, OrderedBookSnapshot] = {}

    def seed(self, snapshot: OrderedBookSnapshot) -> None:
        self.books[snapshot.book_id] = snapshot

    async def find(self, book_id: UUID) -> OrderedBookSnapshot | None:
        return self.books.get(book_id)
