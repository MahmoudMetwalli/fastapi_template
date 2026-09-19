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
"""

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
    this template already has; no use case class needs to change to
    satisfy this, only declare it (see each use case module's
    `if TYPE_CHECKING:` conformance check, matching the convention in
    `application/ports/*.py`).
    """

    async def execute(self, command: C) -> R: ...


class QueryHandler[Q: Query[Any], R](Protocol):
    async def execute(self, query: Q) -> R: ...
