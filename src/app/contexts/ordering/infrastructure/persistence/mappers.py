"""The domain <-> ORM boundary for `ordering`. Same shape as `catalog`'s
`mappers.py`: free functions, and the only module that imports both
`Order` and `OrderRow`/`OrderLineRow`.

Unlike `catalog`'s single-table `Book`/`BookRow`, `to_domain` here
reconstructs `Order.lines` from a list of already-loaded `OrderLineRow`s —
`SqlAlchemyOrderRepository` is responsible for loading them (via
`selectinload`) before a row ever reaches this module.
"""

from app.contexts.ordering.domain.order import Order, OrderId
from app.contexts.ordering.domain.value_objects import OrderedBookSnapshot, OrderLine, Quantity
from app.contexts.ordering.infrastructure.persistence.models import OrderLineRow, OrderRow


def to_domain(row: OrderRow) -> Order:
    return Order(
        id=OrderId(row.id),
        lines=[
            OrderLine(
                snapshot=OrderedBookSnapshot(
                    book_id=line.book_id,
                    title=line.title_snapshot,
                    unit_price_cents=line.unit_price_cents_snapshot,
                ),
                quantity=Quantity(line.quantity),
            )
            for line in row.lines
        ],
    )


def to_row(order: Order) -> OrderRow:
    return OrderRow(
        id=order.id.value,
        lines=[
            OrderLineRow(
                book_id=line.snapshot.book_id,
                title_snapshot=line.snapshot.title,
                unit_price_cents_snapshot=line.snapshot.unit_price_cents,
                quantity=line.quantity.value,
            )
            for line in order.lines
        ],
    )
