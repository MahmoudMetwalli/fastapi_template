"""The `Book` aggregate — the only place catalog business rules live.

No SQLAlchemy import, no Pydantic import, no FastAPI import. Enforced
mechanically by the `import-linter` "Domain is framework-free" contract in
pyproject.toml, not just by convention.
"""

from dataclasses import dataclass

from app.contexts.catalog.domain.events import BookPriceChanged, BookRegistered
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title
from app.shared.domain.entity import AggregateRoot
from app.shared.domain.identifier import EntityId


@dataclass(frozen=True, slots=True)
class BookId(EntityId):
    pass


@dataclass(slots=True, eq=False, kw_only=True)
class Book(AggregateRoot):
    id: BookId
    title: Title
    isbn: Isbn
    price: Money

    @classmethod
    def register(cls, *, title: Title, isbn: Isbn, price: Money) -> Book:
        """Factory: the aggregate is valid the moment it exists — the id is
        minted here, not by the database."""
        book_id = BookId.new()
        book = cls(id=book_id, title=title, isbn=isbn, price=price)
        book.record_event(BookRegistered(book_id=book_id, isbn=str(isbn)))
        return book

    def change_price(self, new_price: Money) -> None:
        if new_price.amount_cents == self.price.amount_cents:
            return
        old_amount_cents = self.price.amount_cents
        self.price = new_price
        self.record_event(
            BookPriceChanged(
                book_id=self.id,
                old_amount_cents=old_amount_cents,
                new_amount_cents=new_price.amount_cents,
            )
        )
