# fastapi-ddd-template

A FastAPI service template built around Domain-Driven Design and Clean
Architecture: bounded contexts, explicit ports, an async SQLAlchemy 2.0
persistence layer, an in-memory event bus (abxbus), and `dependency-injector`
for composition.

Two bounded contexts ship as worked examples: `catalog` (single-context
patterns — aggregate, value objects, repository, a narrowly-scoped Unit of
Work) and `ordering` (everything that only makes sense with *two* contexts
— a Context Map relationship, an Anti-Corruption Layer, an Open Host
Service). See **[docs/ddd-concepts.md](docs/ddd-concepts.md)** for every
DDD concept in this repo mapped to the code that implements it.

## Stack

Python 3.14 · uv · FastAPI · Pydantic v2 + pydantic-settings · SQLAlchemy
2.0 (async) + Alembic · dependency-injector · abxbus · pytest.

## Getting started

```bash
cp .env.example .env
make db-up        # starts Postgres via docker-compose
make migrate       # alembic upgrade head
make dev           # uv run fastapi dev src/app/main.py
```

Then open `http://127.0.0.1:8000/docs`.

```bash
make test-fast     # unit + application tests — no database needed
make test          # the full suite, including integration + e2e (needs Postgres)
make lint          # ruff + mypy --strict + import-linter
```

## Layout

Bounded context first, layers inside each:

```
src/app/
├── containers.py             # the one DI container
├── shared/                    # shared kernel — same layer shape as a context
│   └── infrastructure/
│       ├── database/
│       │   ├── engine.py           # the async engine Resource
│       │   ├── base.py             # declarative Base, naming_convention
│       │   ├── registry.py         # imports every context's models.py, for Alembic
│       │   ├── session_strategy.py # SessionStrategy: OwnSessionFactory / BoundSession
│       │   └── session_scoped.py   # base class every repository/query-service inherits
│       └── events.py               # the abxbus boundary — see below
└── contexts/
    ├── catalog/                  # ← copy this folder to add a context
    │   ├── domain/                # zero third-party imports (lint-enforced)
    │   ├── application/
    │   │   ├── ports/               # Protocols: BookRepository, BookQueryService,
    │   │   │                        # CatalogTransaction
    │   │   ├── commands.py, queries.py, read_models.py
    │   │   └── use_cases/           # one file per use case
    │   ├── infrastructure/
    │   │   └── persistence/
    │   │       ├── models.py         # BookRow — the ORM schema, nothing else
    │   │       ├── mappers.py        # domain <-> ORM, the only file that imports both
    │   │       ├── book_repository.py
    │   │       ├── book_query_service.py
    │   │       ├── transaction.py    # implements CatalogTransaction — see below
    │   │       └── catalog_lookup.py # implements published/lookup.py — see below
    │   ├── presentation/
    │   │   ├── router.py             # FastAPI routes, @inject + Provide[Container...]
    │   │   └── schemas.py            # HTTP request/response models
    │   └── published/                # catalog's *outward* contract — see below
    │       ├── dtos.py                # CatalogBookSummary — the Published Language
    │       └── lookup.py              # CatalogLookup — the Open Host Service
    └── ordering/                 # a second context, to make cross-context
                                   # patterns real rather than hypothetical
        ├── domain/                 # Order aggregate, OrderLine/OrderedBookSnapshot
        ├── application/
        │   ├── ports/                # OrderRepository, and BookCatalog — the seam
        │   │                         # an Anti-Corruption Layer plugs into
        │   └── use_cases/
        ├── infrastructure/
        │   ├── catalog_acl.py        # the Anti-Corruption Layer — see below
        │   └── persistence/
        └── presentation/
```

See `src/app/contexts/catalog/` for the single-context worked example:
registering a book (single or batch), changing its price, fetching one,
and listing them. See `src/app/contexts/ordering/` for the cross-context
one: placing an order looks up book data from `catalog` through an
Anti-Corruption Layer, snapshotting it so a later price change in
`catalog` can never retroactively change an already-placed order's total.
**[docs/ddd-concepts.md](docs/ddd-concepts.md)** walks through every
pattern in both contexts, including the ones neither context needs (yet).

## Adding a new bounded context

**The fast path:**

```bash
uv run python scripts/new_context.py billing --aggregate Invoice
# or: make new-context NAME=billing AGGREGATE=Invoice
```

Scaffolds the four layers with a minimal, working one-field aggregate
(`create`/`get`, wired end to end from domain to HTTP), and — the tedious
part — registers it for you: an import in `registry.py`, an
`include_router(...)` in `router.py`, `Factory` providers in
`containers.py`, and an `"<Your context> layers point inward"`
import-linter contract in `pyproject.toml`. It then runs `ruff` to sort
imports and format the new files. The result passes `mypy --strict` and
`lint-imports` immediately — verified by generating a throwaway context
this way while building this script and running the full verification
suite against it before deleting it. Rename the placeholder `name` field
and `create()`'s invariants to your real ones and go.

It does **not** scaffold a `published/` interface or an Anti-Corruption
Layer for you — see the manual steps below for that, since it only makes
sense once you know which two contexts actually need to talk to each
other.

**What the script does, if you're doing it by hand instead (or extending
the script):**

1. Copy `src/app/contexts/catalog/` to `src/app/contexts/<your_context>/` and
   rework it for your aggregate. Drop the `published/` folder unless another
   context will genuinely need to depend on this one — see below.
2. Add one import line to `src/app/shared/infrastructure/database/registry.py`
   so Alembic sees the new context's tables.
3. Add one `include_router(...)` line to `src/app/router.py`.
4. Register the new context's repositories/query-services and its use cases
   as `Factory` providers in `containers.py` (see `catalog`'s for the
   pattern).
5. Add an `"<Your context> layers point inward"` layers contract for it in
   the `import-linter` contracts in `pyproject.toml`, matching `catalog`'s
   or `ordering`'s.
6. `uv run alembic revision --autogenerate -m "create <context> tables"`.

Only do the following if the new context needs to *depend on* another
existing context (e.g. it needs to look up data another context owns) —
most new contexts don't:

7. Add a `published/` folder to the context being depended on (see
   `catalog/published/` for the shape: a DTO + a `Protocol`, plus an
   implementation in its own `infrastructure/`), if it doesn't have one yet.
8. In the *dependent* context, add your own port for what you need (see
   `ordering/application/ports/book_catalog.py`) and an Anti-Corruption
   Layer implementing it by calling the other context's `published`
   interface and translating the result into your own vocabulary (see
   `ordering/infrastructure/catalog_acl.py`).
9. Wire the translation in `containers.py` — the composition root is the
   only place two contexts should ever be introduced to each other.
10. Add two `forbidden`-type import-linter contracts scoping the
    relationship, matching "Ordering may only depend on catalog's published
    interface" / "Catalog does not depend on ordering" in `pyproject.toml`
    — including *why* they exclude `presentation` (read the comment above
    them; it's a real gotcha, not boilerplate).

See **[docs/ddd-concepts.md](docs/ddd-concepts.md#anti-corruption-layer)**
for why this shape (not a shared type, not a direct import) is the point,
not incidental ceremony.

## Design decisions worth knowing before you extend this

- **Repositories hold a `SessionStrategy`, not a session or a session
  factory directly** (`shared/infrastructure/database/session_strategy.py`).
  `SqlAlchemySessionScoped` (which `SqlAlchemyBookRepository`/
  `SqlAlchemyBookQueryService` inherit) stores one `SessionStrategy` and
  never changes it — no setter, no mutation after construction. That
  immutability is what makes it safe for `book_repository`/
  `book_query_service` to be plain container `Factory` providers used
  concurrently by every request: nothing on the instance ever changes
  between calls, so there's nothing for two concurrent requests to race
  over. `OwnSessionFactory` (the default) opens and closes a fresh session
  per call; `BoundSession` reuses one already-open session for every call
  — used only by `SqlAlchemyCatalogTransaction`, constructed directly with
  the session it just opened (see the next point). An earlier version
  picked the strategy via an `isinstance` check on the constructor
  argument instead of an injected `SessionStrategy` object; formalizing it
  removed that branching without changing behaviour.
- **`CatalogTransaction` exists for the one use case that needs several
  writes to commit or roll back together**: `RegisterBooksBatchUseCase`
  imports a batch of books where one invalid or duplicate entry must undo
  the *whole* batch. A session-per-method repository can't provide that —
  each call would be its own transaction — so this port opens one session
  for a whole `async with` block and exposes repositories bound to it
  (today just `.books`; if `catalog` ever grows a second aggregate, that
  repository's port joins this same one). It's a Unit of Work in shape,
  scoped deliberately to exactly the operation that needs it rather than
  reintroduced as something every request goes through — see
  `application/ports/transaction.py`'s docstring for the full reasoning,
  including why a generic per-request version of this was tried first and
  removed.
- **Never inject a raw `.provider` reference into application code — inject
  the resolved value instead.** An earlier version gave
  `RegisterBooksBatchUseCase` `catalog_transaction.provider` and had it
  call that itself to get a fresh `CatalogTransaction` per batch. Since
  `catalog_transaction` is built from `session_factory` → `engine` (an
  async `Resource`), calling a raw provider reference goes through
  dependency-injector's own resolution machinery *every time it's called*
  — verified to sometimes return the transaction directly and sometimes a
  `Future`, depending on dependency-injector's internal caching state at
  that exact moment, not on anything the calling code controls. It broke
  the running app (`TypeError: '_asyncio.Future' object does not support
  the asynchronous context manager protocol`) on the first request to a
  fresh process, while all 53 automated tests passed — the e2e tier's
  `providers.Object(...)` override (see `tests/e2e/conftest.py`) makes
  `session_factory` synchronous in tests, silently suppressing the exact
  behaviour that broke in production. The real fix wasn't to defensively
  `await`-wrap the call (that would only mask it call-site by call-site) —
  it was to stop handing application code a provider reference at all.
  `containers.py` now injects `catalog_transaction` (a plain `Factory`)
  directly into `register_books_batch_use_case`, exactly like `books`/
  `event_bus` are injected into every other use case: dependency-injector
  does its async resolution *once*, at the point the use case itself is
  built, and the use case only ever holds an already-resolved object. This
  works because one HTTP request resolves the use case once and calls
  `execute()` once — "fresh per resolution" and "fresh per call" are the
  same thing here, so there was never a need for a stored callable in the
  first place.
- **The session never crosses the port boundary.** `BookRepository`,
  `BookQueryService`, and `CatalogTransaction` never mention
  `AsyncSession` — only `infrastructure/` does (`session_strategy.py` and
  the repository/query-service/transaction classes that use it). The
  application layer never needs to import SQLAlchemy to type a
  constructor.
- **`SqlAlchemyCatalogTransaction.__aenter__` constructs
  `SqlAlchemyBookRepository(BoundSession(session))` directly, not through
  the container.** That `session` is created inside `__aenter__` itself,
  at a runtime moment — one specific `async with` block, on one specific
  call — that a container wired once at app startup has no way to reach:
  there is no provider that can represent "the session this particular,
  currently-executing call is about to open." A one-argument, zero-
  collaborator constructor call at the exact point its argument exists is
  the boundary of what dependency injection can do, not a shortcut around
  it.
- **Ports are `typing.Protocol`, not ABC**, and are never explicitly
  subclassed by their implementations — see the comments in
  `application/ports/*.py`. mypy checks Protocol conformance at the *use
  site*, not at the implementation's definition, so each infrastructure
  module ends with a `if TYPE_CHECKING: _: type[Port] = Implementation`
  line that closes that gap. Port attributes (not just methods) are
  declared as read-only `@property`, not plain fields — mypy treats a
  Protocol's plain attribute as invariant (read-write), which fails
  structurally the moment an implementation's attribute is a subtype of
  the port's declared type; a read-only property is covariant instead
  (verified with a minimal repro).
- **No `map_imperatively`.** ORM rows (`*Row` in `infrastructure/persistence
  /models.py`) and domain aggregates are mapped by hand in `mappers.py`.
  Costs a little boilerplate per aggregate; buys a domain layer that is
  never, even accidentally, an ORM-managed object.
- **No module uses `from __future__ import annotations`.** On Python 3.14,
  PEP 649 already gives every module deferred annotation evaluation
  natively — forward references resolve to real objects on first access,
  with no `__future__` import needed. Opting into PEP 563 instead (via the
  `__future__` import) turns annotations into *strings*, which broke
  `dependency-injector`'s `@inject`: its marker detection calls
  `inspect.signature(fn)` expecting a live `Annotated[...]` object, and a
  stringified annotation hides the `Provide[...]` marker inside it, so
  `@inject` silently no-ops. Verified empirically; see
  `contexts/catalog/presentation/router.py`'s module docstring.
- **`app.dependency_overrides` does nothing for anything injected via
  `Provide[]`.** Since every repository/use-case in this template goes
  through the container, that means *everything* — use
  `container.<provider>.override(...)` in tests instead (see
  `tests/e2e/conftest.py`, which overrides `container.session_factory`;
  every repository, query service, transaction, and use case is built
  *from* it, so overriding that one provider is enough for the whole
  graph to point at the test database).

## Growing this template

Deliberately not included yet, in order of when you'll likely need them:

1. **A transactional outbox**, once a context needs to react to another's
   events reliably rather than in-memory/best-effort. `shared/domain
   /events.py` (`AggregateRoot.pull_events()`) and `shared/infrastructure
   /events.py` (`publish()`, the abxbus boundary) already exist; today a use
   case pulls its aggregate's events and publishes them directly, in-memory,
   best-effort — and, for the non-batch use cases, before the request's
   actual commit rather than strictly after it (see `RegisterBookUseCase`).
   Swap the `publish()` call for an outbox-table insert written in the same
   transaction as the aggregate, and add a worker that drains the table.
   `ordering.PlaceOrderUseCase` publishing `OrderPlaced` has the exact same
   gap today; it's the natural next candidate once something actually
   subscribes to it.
2. **`CatalogTransaction` genuinely multi-repository**, once `catalog`
   grows a second aggregate — today it exposes just `.books`; see
   `application/ports/transaction.py`'s docstring.
3. **Auth**, as its own context (`identity`/`auth`), with routes elsewhere
   depending on a plain FastAPI dependency (`app.dependency_overrides`
   still works for *those*, unlike anything wired through `Provide[]`).
4. Caching, background workers, an application Dockerfile, rate limiting.
