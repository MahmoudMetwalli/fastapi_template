"""The domain <-> ORM boundary. Free functions, not methods on `BookRow`
(`fastapi-todo-ddd` puts `to_entity`/`from_entity` on the ORM model itself,
which makes the model responsible for domain invariants) and not
`registry.map_imperatively` (`fastapi-ddd-example`) — see the project
plan's decision #2 for the full reasoning. This is the only module that
imports both `Book` and `BookRow`.

`apply_to_row` mutating the *already-managed* row (rather than building a
fresh `BookRow`) is the load-bearing detail: it's what lets the session
emit an UPDATE at flush instead of a duplicate INSERT.
"""

from app.contexts.catalog.domain.book import Book, BookId
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title
from app.contexts.catalog.infrastructure.persistence.models import BookRow


def to_domain(row: BookRow) -> Book:
    return Book(
        id=BookId(row.id),
        title=Title(row.title),
        isbn=Isbn(row.isbn),
        price=Money(row.price_cents),
    )


def to_row(book: Book) -> BookRow:
    return BookRow(
        id=book.id.value,
        title=str(book.title),
        isbn=str(book.isbn),
        price_cents=book.price.amount_cents,
    )


def apply_to_row(book: Book, row: BookRow) -> None:
    row.title = str(book.title)
    row.isbn = str(book.isbn)
    row.price_cents = book.price.amount_cents
