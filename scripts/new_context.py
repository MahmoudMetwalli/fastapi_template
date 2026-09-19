"""Scaffold a new bounded context: the four layers, a minimal one-field
aggregate wired end-to-end (domain -> repository -> use cases -> HTTP), and
every registration point this template needs a new context added to
(`registry.py`, `router.py`, `containers.py`, and an import-linter "layers"
contract in `pyproject.toml`).

This exists because those registration points are exactly the kind of
boilerplate that's tedious and error-prone by hand, not because a new
context needs anything clever: copying `src/app/contexts/catalog/` and
renaming things by hand (the README's older advice) works fine too, this
just does the same thing without four manual file edits.

Usage:

    uv run python scripts/new_context.py billing --aggregate Invoice

Generates a working, wired, mypy/ruff/import-linter-clean context whose
one aggregate has a single `name: str` field — a starting point to rename
and extend, the same role `catalog`'s `Book` plays as a worked example.
It does NOT scaffold a second context's Anti-Corruption Layer/`published/`
interface: that only makes sense once you know which two contexts actually
need to talk to each other. See README.md's "Adding a new bounded
context", steps 7-10, and docs/ddd-concepts.md's "Anti-Corruption Layer"
section, for that — `src/app/contexts/ordering/` is the worked example.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "src" / "app"


def to_snake(name: str) -> str:
    step = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step).lower()


def render(template: str, *, context: str, aggregate: str, table: str) -> str:
    aggregate_snake = to_snake(aggregate)
    return (
        template.replace("__context__", context)
        .replace("__Aggregate__", aggregate)
        .replace("__aggregate__", aggregate_snake)
        .replace("__table__", table)
    )


AGGREGATE = '''"""`__Aggregate__` — a starting point, not a finished design. Replace
`name` with your real fields, and `create()`'s body with your real
invariants; see `app/contexts/catalog/domain/book.py` for a worked example
of an aggregate with more than one field and more than one behaviour
method.
"""

from dataclasses import dataclass

from app.contexts.__context__.domain.events import __Aggregate__Created
from app.shared.domain.entity import AggregateRoot
from app.shared.domain.identifier import EntityId


@dataclass(frozen=True, slots=True)
class __Aggregate__Id(EntityId):
    pass


@dataclass(slots=True, eq=False, kw_only=True)
class __Aggregate__(AggregateRoot):
    id: __Aggregate__Id
    name: str

    @classmethod
    def create(cls, *, name: str) -> "__Aggregate__":
        __aggregate___id = __Aggregate__Id.new()
        __aggregate__ = cls(id=__aggregate___id, name=name)
        __aggregate__.record_event(__Aggregate__Created(__aggregate___id=__aggregate___id))
        return __aggregate__
'''

ERRORS = '''from app.shared.domain.errors import EntityNotFoundError


class __Aggregate__NotFoundError(EntityNotFoundError):
    def __init__(self, __aggregate___id: object) -> None:
        super().__init__(f"__Aggregate__ {__aggregate___id} was not found")
'''

EVENTS = '''from dataclasses import dataclass

from app.shared.domain.events import DomainEvent
from app.shared.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, kw_only=True)
class __Aggregate__Created(DomainEvent):
    __aggregate___id: EntityId
'''

REPOSITORY_PORT = '''"""A `Protocol`, not explicitly subclassed by its implementation — see
`app/contexts/catalog/application/ports/book_repository.py` for why.
"""

from typing import Protocol

from app.contexts.__context__.domain.__aggregate__ import __Aggregate__, __Aggregate__Id


class __Aggregate__Repository(Protocol):
    async def get(self, __aggregate___id: __Aggregate__Id) -> __Aggregate__ | None: ...

    async def add(self, __aggregate__: __Aggregate__) -> None: ...
'''

COMMANDS = '''from dataclasses import dataclass

from app.contexts.__context__.domain.__aggregate__ import __Aggregate__Id
from app.shared.application.messages import Command


@dataclass(frozen=True, slots=True, kw_only=True)
class Create__Aggregate__Command(Command[__Aggregate__Id]):
    name: str
'''

QUERIES = '''from dataclasses import dataclass
from uuid import UUID

from app.contexts.__context__.application.read_models import __Aggregate__ReadModel
from app.shared.application.messages import Query


@dataclass(frozen=True, slots=True, kw_only=True)
class Get__Aggregate__Query(Query[__Aggregate__ReadModel]):
    __aggregate___id: UUID
'''

READ_MODELS = '''from uuid import UUID

from pydantic import BaseModel, ConfigDict


class __Aggregate__ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    name: str
'''

CREATE_USE_CASE = '''from typing import TYPE_CHECKING

from abxbus import EventBus

from app.contexts.__context__.application.commands import Create__Aggregate__Command
from app.contexts.__context__.application.ports.__aggregate___repository import (
    __Aggregate__Repository,
)
from app.contexts.__context__.domain.__aggregate__ import __Aggregate__, __Aggregate__Id
from app.shared.application.bus import command_handler
from app.shared.application.messages import CommandHandler
from app.shared.infrastructure.events import publish


@command_handler(Create__Aggregate__Command)
class Create__Aggregate__UseCase:
    def __init__(self, __aggregate__s: __Aggregate__Repository, event_bus: EventBus) -> None:
        self._\
__aggregate__s = __aggregate__s
        self._event_bus = event_bus

    async def execute(self, command: Create__Aggregate__Command) -> __Aggregate__Id:
        __aggregate__ = __Aggregate__.create(name=command.name)
        await self._\
__aggregate__s.add(__aggregate__)

        for event in __aggregate__.pull_events():
            await publish(self._event_bus, event)

        return __aggregate__.id


if TYPE_CHECKING:
    _conforms_to_command_handler: type[
        CommandHandler[Create__Aggregate__Command, __Aggregate__Id]
    ] = Create__Aggregate__UseCase
'''

GET_USE_CASE = '''from typing import TYPE_CHECKING

from app.contexts.__context__.application.ports.__aggregate___repository import (
    __Aggregate__Repository,
)
from app.contexts.__context__.application.queries import Get__Aggregate__Query
from app.contexts.__context__.application.read_models import __Aggregate__ReadModel
from app.contexts.__context__.domain.errors import __Aggregate__NotFoundError
from app.contexts.__context__.domain.__aggregate__ import __Aggregate__Id
from app.shared.application.bus import query_handler
from app.shared.application.messages import QueryHandler


@query_handler(Get__Aggregate__Query)
class Get__Aggregate__UseCase:
    def __init__(self, __aggregate__s: __Aggregate__Repository) -> None:
        self._\
__aggregate__s = __aggregate__s

    async def execute(self, query: Get__Aggregate__Query) -> __Aggregate__ReadModel:
        __aggregate__ = await self._\
__aggregate__s.get(__Aggregate__Id(query.__aggregate___id))
        if __aggregate__ is None:
            raise __Aggregate__NotFoundError(query.__aggregate___id)
        return __Aggregate__ReadModel(id=__aggregate__.id.value, name=__aggregate__.name)


if TYPE_CHECKING:
    _conforms_to_query_handler: type[
        QueryHandler[Get__Aggregate__Query, __Aggregate__ReadModel]
    ] = Get__Aggregate__UseCase
'''

MODELS = '''import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database.base import Base


class __Aggregate__Row(Base):
    __tablename__ = "__table__"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
'''

MAPPERS = '''from app.contexts.__context__.domain.__aggregate__ import __Aggregate__, __Aggregate__Id
from app.contexts.__context__.infrastructure.persistence.models import __Aggregate__Row


def to_domain(row: __Aggregate__Row) -> __Aggregate__:
    return __Aggregate__(id=__Aggregate__Id(row.id), name=row.name)


def to_row(__aggregate__: __Aggregate__) -> __Aggregate__Row:
    return __Aggregate__Row(id=__aggregate__.id.value, name=__aggregate__.name)
'''

REPOSITORY_IMPL = '''from typing import TYPE_CHECKING

from app.contexts.__context__.application.ports.__aggregate___repository import (
    __Aggregate__Repository,
)
from app.contexts.__context__.domain.__aggregate__ import __Aggregate__, __Aggregate__Id
from app.contexts.__context__.infrastructure.persistence.mappers import to_domain, to_row
from app.contexts.__context__.infrastructure.persistence.models import __Aggregate__Row
from app.shared.infrastructure.database.session_scoped import SqlAlchemySessionScoped


class SqlAlchemy__Aggregate__Repository(SqlAlchemySessionScoped):
    async def get(self, __aggregate___id: __Aggregate__Id) -> __Aggregate__ | None:
        async with self._strategy.session() as session:
            row = await session.get(__Aggregate__Row, __aggregate___id.value)
            return to_domain(row) if row is not None else None

    async def add(self, __aggregate__: __Aggregate__) -> None:
        async with self._strategy.session() as session:
            session.add(to_row(__aggregate__))


if TYPE_CHECKING:
    _conforms_to_\
__aggregate___repository: type[__Aggregate__Repository] = SqlAlchemy__Aggregate__Repository
'''

SCHEMAS = '''from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.shared.presentation.schemas import ApiModel


class Create__Aggregate__Request(ApiModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]


class __Aggregate__CreatedResponse(ApiModel):
    id: UUID


class __Aggregate__Response(ApiModel):
    id: UUID
    name: str
'''

ROUTER = '''from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.containers import Container
from app.contexts.__context__.application.commands import Create__Aggregate__Command
from app.contexts.__context__.application.queries import Get__Aggregate__Query
from app.contexts.__context__.presentation.schemas import (
    Create__Aggregate__Request,
    __Aggregate__CreatedResponse,
    __Aggregate__Response,
)
from app.shared.application.bus import CommandBus, QueryBus

router = APIRouter(prefix="/__table__", tags=["__context__"])

Commands = Annotated[CommandBus, Depends(Provide[Container.command_bus])]
Queries = Annotated[QueryBus, Depends(Provide[Container.query_bus])]


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create___aggregate__(
    payload: Create__Aggregate__Request, bus: Commands
) -> __Aggregate__CreatedResponse:
    __aggregate___id = await bus.dispatch(Create__Aggregate__Command(name=payload.name))
    return __Aggregate__CreatedResponse(id=__aggregate___id.value)


@router.get("/{__aggregate___id}")
@inject
async def get___aggregate__(__aggregate___id: UUID, bus: Queries) -> __Aggregate__Response:
    read_model = await bus.dispatch(Get__Aggregate__Query(__aggregate___id=__aggregate___id))
    return __Aggregate__Response.model_validate(read_model)
'''

FILES: dict[str, str] = {
    "domain/__aggregate__.py": AGGREGATE,
    "domain/errors.py": ERRORS,
    "domain/events.py": EVENTS,
    "application/ports/__aggregate___repository.py": REPOSITORY_PORT,
    "application/commands.py": COMMANDS,
    "application/queries.py": QUERIES,
    "application/read_models.py": READ_MODELS,
    "application/use_cases/create___aggregate__.py": CREATE_USE_CASE,
    "application/use_cases/get___aggregate__.py": GET_USE_CASE,
    "infrastructure/persistence/models.py": MODELS,
    "infrastructure/persistence/mappers.py": MAPPERS,
    "infrastructure/persistence/__aggregate___repository.py": REPOSITORY_IMPL,
    "presentation/schemas.py": SCHEMAS,
    "presentation/router.py": ROUTER,
}

EMPTY_DIRS = [
    "domain",
    "application",
    "application/ports",
    "application/use_cases",
    "infrastructure",
    "infrastructure/persistence",
    "presentation",
]


def write_context(*, context: str, aggregate: str, table: str) -> Path:
    context_dir = APP / "contexts" / context
    if context_dir.exists():
        print(f"error: {context_dir} already exists", file=sys.stderr)
        raise SystemExit(1)

    (context_dir).mkdir(parents=True)
    (context_dir / "__init__.py").write_text("")
    for rel_dir in EMPTY_DIRS:
        d = context_dir / rel_dir
        d.mkdir(parents=True, exist_ok=True)
        (d / "__init__.py").write_text("")

    for rel_path, template in FILES.items():
        rel_path = render(rel_path, context=context, aggregate=aggregate, table=table)
        content = render(template, context=context, aggregate=aggregate, table=table)
        path = context_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    return context_dir


def append_to_registry(*, context: str) -> None:
    path = APP / "shared" / "infrastructure" / "database" / "registry.py"
    line = (
        f"from app.contexts.{context}.infrastructure.persistence "
        f"import models as _{context}_models  # noqa: F401\n"
    )
    text = path.read_text()
    if line in text:
        return
    path.write_text(text.rstrip("\n") + "\n" + line)


def insert_into_router(*, context: str) -> None:
    path = APP / "router.py"
    text = path.read_text()
    import_line = (
        f"from app.contexts.{context}.presentation.router import router as {context}_router\n"
    )
    include_line = f"api_router.include_router({context}_router)\n"
    if import_line in text:
        return

    anchor = "api_router = APIRouter()\n"
    if anchor not in text:
        print(f"warning: could not find {anchor!r} in {path}; add the import/include manually")
        return
    text = text.replace(anchor, import_line + "\n" + anchor)
    text = text.rstrip("\n") + "\n" + include_line
    path.write_text(text)


def insert_into_containers(*, context: str, aggregate: str) -> None:
    path = APP / "containers.py"
    text = path.read_text()
    aggregate_snake = to_snake(aggregate)

    import_lines = (
        f"from app.contexts.{context}.application.use_cases.create_{aggregate_snake} "
        f"import Create{aggregate}UseCase\n"
        f"from app.contexts.{context}.application.use_cases.get_{aggregate_snake} "
        f"import Get{aggregate}UseCase\n"
        f"from app.contexts.{context}.infrastructure.persistence.{aggregate_snake}_repository "
        f"import SqlAlchemy{aggregate}Repository\n"
    )
    if import_lines in text:
        return

    anchor = "from app.shared.application.bus import CommandBus, QueryBus\n"
    if anchor not in text:
        print(f"warning: could not find import anchor in {path}; add these imports manually:\n"
              f"{import_lines}")
    else:
        text = text.replace(anchor, import_lines + anchor)

    provider_block = (
        f"    {aggregate_snake}_repository = providers.Factory(\n"
        f"        SqlAlchemy{aggregate}Repository, strategy=own_session_factory_strategy\n"
        f"    )\n"
        f"    create_{aggregate_snake}_use_case = providers.Factory(\n"
        f"        Create{aggregate}UseCase, {aggregate_snake}s={aggregate_snake}_repository, "
        f"event_bus=event_bus\n"
        f"    )\n"
        f"    get_{aggregate_snake}_use_case = providers.Factory(\n"
        f"        Get{aggregate}UseCase, {aggregate_snake}s={aggregate_snake}_repository\n"
        f"    )\n\n"
    )
    # Inserted right before `command_bus`, not at EOF: every use case the
    # buses list must already be defined above them.
    command_bus_anchor = "    command_bus = providers.Factory("
    if command_bus_anchor not in text:
        print(
            f"warning: could not find {command_bus_anchor!r} in {path}; "
            f"add these providers manually:\n{provider_block}"
        )
    else:
        text = text.replace(command_bus_anchor, provider_block + command_bus_anchor, 1)

    # Register the new handlers into command_bus's/query_bus's providers.List(...) —
    # each bus's list closes with "        ),\n    )" immediately followed by
    # either the next bus or end of file.
    command_bus_close = "        ),\n    )\n    query_bus = providers.Factory("
    if command_bus_close in text:
        text = text.replace(
            command_bus_close,
            f"            create_{aggregate_snake}_use_case,\n{command_bus_close}",
            1,
        )
    else:
        print(
            "warning: could not register the new command handler into command_bus's "
            f"providers.List(...); add `create_{aggregate_snake}_use_case,` to it manually."
        )

    last_close = text.rfind("        ),\n    )")
    if last_close == -1:
        print(
            "warning: could not register the new query handler into query_bus's "
            f"providers.List(...); add `get_{aggregate_snake}_use_case,` to it manually."
        )
    else:
        insertion = f"            get_{aggregate_snake}_use_case,\n"
        text = text[:last_close] + insertion + text[last_close:]

    path.write_text(text)


def insert_into_pyproject(*, context: str) -> None:
    path = REPO_ROOT / "pyproject.toml"
    text = path.read_text()

    domain_free_anchor = '    "app.shared.domain",\n]'
    domain_free_replacement = f'    "app.contexts.{context}.domain",\n    "app.shared.domain",\n]'
    if domain_free_anchor in text and f'"app.contexts.{context}.domain"' not in text:
        text = text.replace(domain_free_anchor, domain_free_replacement, 1)
    else:
        print(
            "warning: could not extend \"Domain is framework-free\" contract automatically; "
            f'add "app.contexts.{context}.domain" to its source_modules list by hand.'
        )

    new_contract = (
        f"[[tool.importlinter.contracts]]\n"
        f'name = "{context.capitalize()} layers point inward"\n'
        f'type = "layers"\n'
        f'layers = ["presentation", "infrastructure", "application", "domain"]\n'
        f'containers = ["app.contexts.{context}"]\n\n'
    )
    # Anchor on the "Shared kernel layers point inward" contract's *name*
    # line, not its preceding comment (which changes wording over time) —
    # then walk back to the "[[tool.importlinter.contracts]]" marker that
    # opens that same block, and insert the new contract right before it.
    shared_name_line = 'name = "Shared kernel layers point inward"'
    if f'name = "{context.capitalize()} layers point inward"' in text:
        pass
    else:
        name_idx = text.find(shared_name_line)
        block_start = text.rfind("[[tool.importlinter.contracts]]", 0, name_idx) if name_idx != -1 else -1
        if name_idx == -1 or block_start == -1:
            print(
                "warning: could not insert a layers contract automatically; add one for "
                f"'{context}' to pyproject.toml by hand, matching catalog's or ordering's."
            )
        else:
            text = text[:block_start] + new_contract + text[block_start:]

    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context", help="snake_case bounded context name, e.g. billing")
    parser.add_argument(
        "--aggregate",
        required=True,
        help="PascalCase aggregate root name for the starting example, e.g. Invoice",
    )
    args = parser.parse_args()

    context = args.context
    aggregate = args.aggregate
    if not re.fullmatch(r"[a-z][a-z0-9_]*", context):
        parser.error("context must be snake_case, e.g. 'billing'")
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", aggregate):
        parser.error("--aggregate must be PascalCase, e.g. 'Invoice'")
    table = to_snake(aggregate) + "s"

    context_dir = write_context(context=context, aggregate=aggregate, table=table)
    append_to_registry(context=context)
    insert_into_router(context=context)
    insert_into_containers(context=context, aggregate=aggregate)
    insert_into_pyproject(context=context)

    print(f"Created {context_dir.relative_to(REPO_ROOT)}, wired into registry.py, router.py, "
          f"containers.py, and pyproject.toml's import-linter contracts.")

    print("Formatting and sorting imports with ruff...")
    subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", "src"], cwd=REPO_ROOT, check=False
    )
    subprocess.run(["uv", "run", "ruff", "format", "src"], cwd=REPO_ROOT, check=False)

    print(
        "\nNext steps:\n"
        f"  1. Replace {aggregate}'s placeholder `name` field and `create()`'s body in\n"
        f"     {context_dir.relative_to(REPO_ROOT)}/domain/{to_snake(aggregate)}.py "
        "with your real fields and invariants.\n"
        "  2. uv run mypy src && uv run lint-imports   # confirm the new context is clean\n"
        f'  3. uv run alembic revision --autogenerate -m "create {table} table"\n'
        "  4. uv run pytest tests/unit tests/application   # no database needed yet\n"
        "\nIf this context needs to depend on another one, don't hand-wire an import between "
        "them — see README.md's \"Adding a new bounded context\", steps 7-10, and "
        "docs/ddd-concepts.md's \"Anti-Corruption Layer\" section for the pattern "
        "(src/app/contexts/ordering/ is the worked example)."
    )


if __name__ == "__main__":
    main()
