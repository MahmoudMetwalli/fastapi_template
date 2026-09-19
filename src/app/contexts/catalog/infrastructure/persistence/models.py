"""The ORM schema for `catalog`, and nothing else — no mapping logic, no
domain invariants. `BookRow`, not `BookEntity`: in DDD "entity" names the
*domain* object, and reusing it for the ORM class (as `fastapi-ddd-example`
does) is what makes `mappers.py` confusing to read.

Declarative `Mapped[]`/`mapped_column`, not `registry.map_imperatively` —
see the project plan's decision #2 for why classical mapping was dropped.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database.base import Base


class BookRow(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    price_cents: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
