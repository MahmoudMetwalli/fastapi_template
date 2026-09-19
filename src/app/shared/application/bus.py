"""The dispatch mechanism routers use instead of importing a specific use
case class per route. A use case declares what it handles right on itself
— `@command_handler(RegisterBookCommand)` above the class, mirroring
NestJS's `@nestjs/cqrs` (`@CommandHandler(SomeCommand)` +
`implements ICommandHandler<SomeCommand>`) — and `containers.py` only
needs to list *instances*; it never re-states which command each one
handles a second time in a hand-maintained dict.

The split across two mechanisms is deliberate, not an oversight:

- `@command_handler(X)`/`@query_handler(X)` are a **runtime** registration
  side effect, purely bookkeeping — they hand the decorated class back
  unchanged (verified with `reveal_type()` — the decorator is fully
  type-preserving) and record `{handler class: command type}` in this
  module's registry, for `CommandBus`/`QueryBus` to read at construction
  time. They do **not** statically verify the handler actually implements
  `CommandHandler[X, R]` for the right `R` — a generic decorator factory
  can't express "constrain the decorated class against the type argument
  from an earlier call" precisely enough for mypy to check it (confirmed
  empirically: a `Protocol` with a generic `__call__` looked like the
  right tool but mypy rejects matching a plain function against it).
- Each handler's own `if TYPE_CHECKING: _conforms_to_command_handler:
  type[CommandHandler[X, R]] = TheUseCase` line (see any file under
  `application/use_cases/`) is what closes that gap statically — the same
  pattern this template already uses for every port
  (`application/ports/*.py`), applied here too. Two mechanisms, each
  catching a different mistake: the decorator catches "forgot to register
  a handler" (a clear `ValueError` at container-build time, not a request-
  time `KeyError`); the `TYPE_CHECKING` line catches "registered a handler
  with the wrong signature."

**Commands and queries have exactly one handler each — unlike domain
events, which fan out to every subscriber via abxbus** (see
`shared/infrastructure/events.py`). `CommandBus`/`QueryBus` enforce that:
constructing one raises if two handlers declare the same command/query
type, and `dispatch` raises a clear error naming the command/query type if
none does — nothing here ever silently does nothing.
"""

from collections.abc import Callable, Iterable
from typing import Any, cast

from app.shared.application.messages import Command, CommandHandler, Query, QueryHandler

_COMMAND_TYPES_BY_HANDLER: dict[type, type[Command[Any]]] = {}
_QUERY_TYPES_BY_HANDLER: dict[type, type[Query[Any]]] = {}


def command_handler[C: Command[Any], H](command_type: type[C]) -> Callable[[type[H]], type[H]]:
    """Class decorator: declares that a use case handles `command_type`.
    See this module's docstring for what it does and doesn't check."""

    def decorator(handler_cls: type[H]) -> type[H]:
        _COMMAND_TYPES_BY_HANDLER[handler_cls] = command_type
        return handler_cls

    return decorator


def query_handler[Q: Query[Any], H](query_type: type[Q]) -> Callable[[type[H]], type[H]]:
    def decorator(handler_cls: type[H]) -> type[H]:
        _QUERY_TYPES_BY_HANDLER[handler_cls] = query_type
        return handler_cls

    return decorator


class CommandBus:
    def __init__(self, handlers: Iterable[CommandHandler[Any, Any]]) -> None:
        self._handlers: dict[type[Command[Any]], CommandHandler[Any, Any]] = {}
        for handler in handlers:
            command_type = _COMMAND_TYPES_BY_HANDLER.get(type(handler))
            if command_type is None:
                raise ValueError(
                    f"{type(handler).__name__} is not decorated with @command_handler(...)"
                )
            if command_type in self._handlers:
                raise ValueError(f"{command_type.__name__} already has a registered handler")
            self._handlers[command_type] = handler

    async def dispatch[R](self, command: Command[R]) -> R:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise ValueError(f"No handler registered for {type(command).__name__}")
        result = await handler.execute(command)
        return cast(R, result)


class QueryBus:
    def __init__(self, handlers: Iterable[QueryHandler[Any, Any]]) -> None:
        self._handlers: dict[type[Query[Any]], QueryHandler[Any, Any]] = {}
        for handler in handlers:
            query_type = _QUERY_TYPES_BY_HANDLER.get(type(handler))
            if query_type is None:
                raise ValueError(
                    f"{type(handler).__name__} is not decorated with @query_handler(...)"
                )
            if query_type in self._handlers:
                raise ValueError(f"{query_type.__name__} already has a registered handler")
            self._handlers[query_type] = handler

    async def dispatch[R](self, query: Query[R]) -> R:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise ValueError(f"No handler registered for {type(query).__name__}")
        result = await handler.execute(query)
        return cast(R, result)
