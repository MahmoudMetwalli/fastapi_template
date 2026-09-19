"""Unit tests for the generic `CommandBus`/`QueryBus` dispatch mechanism,
independent of any specific context's commands/queries — see
`tests/application/catalog/` and `tests/application/ordering/` for the
buses exercised with this template's real commands and queries.
"""

import pytest

from app.shared.application.bus import CommandBus, QueryBus, command_handler, query_handler
from app.shared.application.messages import Command, Query


class _Ping(Command[str]):
    pass


class _NoHandler(Command[None]):
    pass


@command_handler(_Ping)
class _PingHandler:
    async def execute(self, command: _Ping) -> str:
        return "pong"


class _UndecoratedCommandHandler:
    async def execute(self, command: _Ping) -> str:
        return "should never be reached"


class TestCommandBus:
    async def test_dispatches_to_the_registered_handler(self) -> None:
        bus = CommandBus([_PingHandler()])

        assert await bus.dispatch(_Ping()) == "pong"

    async def test_raises_a_clear_error_for_an_unregistered_command(self) -> None:
        bus = CommandBus([_PingHandler()])

        with pytest.raises(ValueError, match="_NoHandler"):
            await bus.dispatch(_NoHandler())

    def test_raises_if_a_handler_has_no_command_handler_decoration(self) -> None:
        with pytest.raises(ValueError, match="not decorated"):
            CommandBus([_UndecoratedCommandHandler()])

    def test_raises_if_two_handlers_declare_the_same_command(self) -> None:
        with pytest.raises(ValueError, match="already has a registered handler"):
            CommandBus([_PingHandler(), _PingHandler()])


class _Question(Query[str]):
    pass


class _UnansweredQuestion(Query[str]):
    pass


@query_handler(_Question)
class _QuestionHandler:
    async def execute(self, query: _Question) -> str:
        return "42"


class _UndecoratedQueryHandler:
    async def execute(self, query: _Question) -> str:
        return "should never be reached"


class TestQueryBus:
    async def test_dispatches_to_the_registered_handler(self) -> None:
        bus = QueryBus([_QuestionHandler()])

        assert await bus.dispatch(_Question()) == "42"

    async def test_raises_a_clear_error_for_an_unregistered_query(self) -> None:
        bus = QueryBus([_QuestionHandler()])

        with pytest.raises(ValueError, match="_UnansweredQuestion"):
            await bus.dispatch(_UnansweredQuestion())

    def test_raises_if_a_handler_has_no_query_handler_decoration(self) -> None:
        with pytest.raises(ValueError, match="not decorated"):
            QueryBus([_UndecoratedQueryHandler()])

    def test_raises_if_two_handlers_declare_the_same_query(self) -> None:
        with pytest.raises(ValueError, match="already has a registered handler"):
            QueryBus([_QuestionHandler(), _QuestionHandler()])
