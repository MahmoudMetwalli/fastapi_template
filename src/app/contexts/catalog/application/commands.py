"""Write-side input. Frozen dataclasses carrying primitives only — a
command must not import Pydantic or FastAPI, since it's transport-agnostic
intent, not an HTTP schema. Compare to `fastapi-todo-ddd`'s use cases, which
are invoked as `use_case((data,))` with a bare positional tuple; a named,
typed command is both readable and type-checkable at the call site.

Each command subclasses `Command[R]` (`shared/application/messages.py`),
`R` being its use case's `execute()` return type — this is what lets
`CommandBus.dispatch(RegisterBookCommand(...))`
(`presentation/router.py`) come back as a real `BookId`, not `Any`.
`RegisterBookBatchItem` doesn't: it's a plain value carried *inside*
`RegisterBooksBatchCommand.items`, never dispatched on its own.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.contexts.catalog.domain.book import BookId
from app.shared.application.messages import Command


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterBookCommand(Command[BookId]):
    title: str
    isbn: str
    price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeBookPriceCommand(Command[None]):
    book_id: UUID
    new_price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterBookBatchItem:
    title: str
    isbn: str
    price_cents: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterBooksBatchCommand(Command[list[BookId]]):
    items: Sequence[RegisterBookBatchItem]
