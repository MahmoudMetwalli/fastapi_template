"""Value objects for `ordering`. `OrderedBookSnapshot` is deliberately
`ordering`'s *own* vocabulary for "a book" — a different type from
`catalog.published.dtos.CatalogBookSummary`, even though the two currently
carry similar fields. Nothing in this module, or anywhere else in
`app.contexts.ordering.domain`/`application`, imports anything from
`catalog`; see `infrastructure/catalog_acl.py` for the one place that
translation happens.
"""

from dataclasses import dataclass
from uuid import UUID

from app.contexts.ordering.domain.errors import QuantityMustBePositiveError


@dataclass(frozen=True, slots=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise QuantityMustBePositiveError(self.value)


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderedBookSnapshot:
    """What `ordering` knows about a book, captured *at order time* — not
    a live reference to `catalog`'s `Book`. If tomorrow's catalog price
    changes, an order placed today must not silently change total with it;
    a snapshot, copied once at the moment of ordering, is how one bounded
    context protects its own history from another context's later
    changes."""

    book_id: UUID
    title: str
    unit_price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderLine:
    snapshot: OrderedBookSnapshot
    quantity: Quantity

    @property
    def subtotal_cents(self) -> int:
        return self.snapshot.unit_price_cents * self.quantity.value
