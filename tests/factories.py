"""Domain object builders: tests state only what they care about."""

from uuid import UUID, uuid4

from app.contexts.catalog.domain.book import Book
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title
from app.contexts.ordering.domain.value_objects import OrderedBookSnapshot


def make_isbn(seed: int = 0) -> str:
    """A syntactically valid ISBN-13 (correct checksum digit), distinct per
    `seed`, for tests that need more than one valid ISBN."""
    twelve_digits = f"978{seed:09d}"
    total = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(twelve_digits))
    check_digit = (10 - total % 10) % 10
    return f"{twelve_digits}{check_digit}"


def make_book(
    *,
    title: str = "Domain-Driven Design",
    isbn: str | None = None,
    price_cents: int = 4999,
) -> Book:
    book = Book.register(
        title=Title(title),
        isbn=Isbn(isbn if isbn is not None else make_isbn()),
        price=Money(price_cents),
    )
    # `Book.register` records a `BookRegistered` event. In production that
    # event is drained by `RegisterBookUseCase` in the same call that
    # creates the book, and anything fetched later via a repository is
    # freshly mapped with no events attached (see
    # `infrastructure/persistence/mappers.py::to_domain`). This factory is
    # almost always used to set up *existing* state for a test of some
    # other operation, so it discards the registration event here too —
    # otherwise a test using the in-memory fake repository (which hands
    # back the same live object, unlike a real DB round trip) would see a
    # stray `BookRegistered` alongside whatever event the operation under
    # test actually produces.
    book.pull_events()
    return book


def make_ordered_book_snapshot(
    *,
    book_id: UUID | None = None,
    title: str = "Domain-Driven Design",
    unit_price_cents: int = 4999,
) -> OrderedBookSnapshot:
    return OrderedBookSnapshot(
        book_id=book_id if book_id is not None else uuid4(),
        title=title,
        unit_price_cents=unit_price_cents,
    )
