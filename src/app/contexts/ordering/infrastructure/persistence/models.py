"""The ORM schema for `ordering`. Two tables, not one JSON column — an
`Order`'s lines are a genuine one-to-many relationship, worth demonstrating
in a template that otherwise only has single-table aggregates
(`catalog.Book`).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.database.base import Base


class OrderRow(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lines: Mapped[list[OrderLineRow]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderLineRow.id"
    )


class OrderLineRow(Base):
    __tablename__ = "order_lines"

    # A plain surrogate PK, not a domain id: `OrderLine` is a value object
    # (see `domain/value_objects.py`), so it has no identity of its own —
    # this key exists only so the relational row can exist at all, and
    # `mappers.py` never reads it back into the domain model. Contrast
    # `OrderRow.id`, which *is* `Order`'s real domain identifier.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    book_id: Mapped[uuid.UUID] = mapped_column()
    title_snapshot: Mapped[str] = mapped_column(String(200))
    unit_price_cents_snapshot: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[OrderRow] = relationship(back_populates="lines")
