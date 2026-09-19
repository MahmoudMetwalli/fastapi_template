"""Base type for aggregate/entity identifiers.

IDs are minted in the domain, at construction time — never assigned by a
database auto-increment — so an aggregate is valid the instant it exists.

`uuid.uuid7()` is stdlib as of Python 3.13/3.14: verified present on this
project's Python 3.14.7. It is time-sortable (good B-tree locality, unlike
uuid4) and needs no coordination (unlike a hand-rolled Snowflake generator,
which needs a configured, unique worker id). Do not reintroduce Snowflake.
"""

import uuid
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class EntityId:
    """Base class for typed identifiers. Subclass per aggregate, e.g.:

    @dataclass(frozen=True, slots=True)
    class BookId(EntityId):
        pass

    book_id = BookId.new()
    """

    value: uuid.UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid.uuid7())

    @classmethod
    def from_string(cls, raw: str) -> Self:
        return cls(uuid.UUID(raw))

    def __str__(self) -> str:
        return str(self.value)
