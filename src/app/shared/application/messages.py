"""`Command[R]`/`Query[R]` carry their result type as a type parameter —
mirroring the shape of MediatR's `IRequest<TResponse>` — so that
`CommandBus.dispatch`/`QueryBus.dispatch` (`bus.py`) can return the
concrete result type `R` at the call site, not `Any`, despite the bus's
internal command-type -> handler lookup being necessarily type-erased (a
plain `dict[type, object]` can't carry a different generic binding per
entry). Verified empirically with `reveal_type()` and a deliberately wrong
handler signature before wiring this into every route — see
`docs/ddd-concepts.md`'s "Command/Query Bus" section for the write-up and
the tradeoff this buys and costs.

`Command`/`Query` are separate (rather than one `Message[R]` base) for the
same reason `application/commands.py` and `application/queries.py` are
separate files in every context: a command mutates state, a query never
does, and keeping the types apart makes that distinction checkable rather
than just a naming convention.

`CommandHandler`/`QueryHandler`'s `execute` is `@abstractmethod`, and every
use case explicitly inherits its specific `CommandHandler[X, R]`/
`QueryHandler[X, R]` (e.g. `class RegisterBookUseCase(CommandHandler
[RegisterBookCommand, BookId]):`) rather than only matching it
structurally. That combination is what makes conformance genuinely
enforced instead of merely intended: a wrong `execute` signature is a
`mypy` error at the class definition itself, and a forgotten `execute`
override raises `TypeError` the moment anything constructs the class
(verified empirically — see `docs/ddd-concepts.md`'s "Command/Query Bus"
section) rather than silently satisfying nothing. This is why no port or
handler protocol in this template is used purely structurally any more —
see `application/ports/book_repository.py` for the same pattern applied
to repositories.
"""

from abc import abstractmethod
from typing import Any, Protocol


class Command[R]:
    """Marker base for a command. Subclass alongside a dataclass decorator:

    @dataclass(frozen=True, slots=True, kw_only=True)
    class RegisterBookCommand(Command[BookId]):
        title: str
        isbn: str
        price_cents: int
    """


class Query[R]:
    """Marker base for a query — same shape as `Command[R]`, for reads."""


class CommandHandler[C: Command[Any], R](Protocol):
    """What a use case must look like to handle a `Command[R]` — note this
    is exactly the `execute(command) -> result` shape every use case in
    this template already has. Each use case explicitly declares which one
    it implements, e.g. `class RegisterBookUseCase(CommandHandler
    [RegisterBookCommand, BookId]):` — see this module's docstring for why.
    """

    @abstractmethod
    async def execute(self, command: C) -> R: ...


class QueryHandler[Q: Query[Any], R](Protocol):
    @abstractmethod
    async def execute(self, query: Q) -> R: ...
