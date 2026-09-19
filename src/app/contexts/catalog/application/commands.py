"""Write-side input. Frozen dataclasses carrying primitives only — a
command must not import Pydantic or FastAPI, since it's transport-agnostic
intent, not an HTTP schema. Compare to `fastapi-todo-ddd`'s use cases, which
are invoked as `use_case((data,))` with a bare positional tuple; a named,
typed command is both readable and type-checkable at the call site.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterBookCommand:
    title: str
    isbn: str
    price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeBookPriceCommand:
    book_id: UUID
    new_price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterBookBatchItem:
    title: str
    isbn: str
    price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterBooksBatchCommand:
    items: Sequence[RegisterBookBatchItem]
