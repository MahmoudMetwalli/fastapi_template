# DDD concepts, and where they live in this repo

Every concept below is backed by real, tested code — not a hypothetical.
Where a concept isn't implemented (a couple aren't), that's said explicitly,
along with why and when you'd reach for it.

The two contexts referenced throughout: `catalog` (books, prices) and
`ordering` (placing an order for books). They exist specifically so
context-boundary concepts — which need *two* contexts to mean anything —
have real code to point at, not just prose.

## Bounded Context

A bounded context is the boundary inside which a model, and the words used
to describe it, mean one specific thing — and outside of which the same
word can mean something else entirely. `src/app/contexts/catalog/` and
`src/app/contexts/ordering/` are the two bounded contexts in this repo.

The clearest evidence a boundary is real: **"a book" means two different
things on either side of it**, deliberately:

| | `catalog.domain.book.Book` | `ordering.domain.value_objects.OrderedBookSnapshot` |
|---|---|---|
| Represents | The book, as catalog manages it | What was true about a book *at the moment it was ordered* |
| Has | An ISBN, a live, changeable price | A title and price frozen at order time, no ISBN |
| Changes over time? | Yes — `change_price()` | No — immutable, forever |

Neither type knows the other exists. This isn't duplication to eliminate;
collapsing them into one shared `Book` type is exactly the mistake a
bounded context boundary exists to prevent — see [Anti-Corruption
Layer](#anti-corruption-layer) for what breaks if you do.

**Enforced, not just documented.** The `import-linter` contracts in
`pyproject.toml` ("Catalog layers point inward", "Ordering layers point
inward", "Ordering may only depend on catalog's published interface",
"Catalog does not depend on ordering") make the boundary a CI-checked fact.
Run `uv run lint-imports` after importing something you shouldn't and watch
it fail.

## Ubiquitous Language

The vocabulary a bounded context's code uses should be the same vocabulary
its domain experts use — not a translation layer in either direction. This
is why `Book.register()` (not `Book.create()` or `Book.insert()`) and
`Order.place()` (not `Order.create()`): "register a book" and "place an
order" are what a person would actually say. It's also why `Isbn`, `Money`,
and `Quantity` are real types instead of `str`/`int` — the language has
words for these things, so the code should too, rather than passing bare
primitives around and re-deriving their meaning from context every time.

The language is *local* to its context, which is the other half of the
point: `ordering`'s `OrderedBookSnapshot` and `catalog`'s `Book` are both
valid, non-competing answers to "what is a book," because the language is
scoped per bounded context, not global to the whole system. See [Bounded
Context](#bounded-context) above.

## Context Map

A Context Map names the *relationship* between two bounded contexts — DDD
doesn't assume every pair of contexts relates the same way. This template
implements one relationship for real; the others are explained here so
you know which to reach for when `ordering`/`catalog` isn't your shape.

**Implemented: Open Host Service + Published Language (supplier side),
Anti-Corruption Layer (consumer side).** `catalog` is the upstream
("supplier") context. Rather than letting every downstream consumer poke
around inside its domain model, it exposes one deliberate, stable interface
— `catalog/published/lookup.py`'s `CatalogLookup`, returning
`catalog/published/dtos.py`'s `CatalogBookSummary` — and nothing else. That
pair *is* an Open Host Service (the interface) publishing a Published
Language (the DTO shape). `ordering` is the downstream ("customer")
context; instead of consuming `catalog`'s internals directly, it goes
through its own [Anti-Corruption Layer](#anti-corruption-layer). See that
section for the full mechanics.

**Not implemented here — what the other relationships mean:**

- **Shared Kernel** — two contexts deliberately share a *slice* of model
  (types, not just infrastructure) and coordinate changes to it together.
  This repo's `app.shared` is infrastructure/plumbing (session strategy,
  event bus wiring, base error types) — not a shared kernel in the DDD
  sense, because it carries no context-specific *business* model. A real
  Shared Kernel would be, e.g., two contexts agreeing to both depend on one
  `Money` type because a currency mismatch between them would itself be a
  bug. Costs coordination: neither side can change the shared part alone.
- **Customer–Supplier** — like OHS/ACL, but the upstream team's roadmap
  formally accounts for the downstream team's needs (planning meetings,
  negotiated interfaces) rather than downstream just adapting to whatever
  upstream publishes. Same code shape as this template's relationship;
  the difference is organizational, not technical.
- **Conformist** — the downstream context gives up on translating the
  upstream model at all and just uses it as-is. Cheaper than an ACL (no
  translation code to write or maintain) but couples you completely to
  someone else's model, including its accidents. Reach for this when the
  upstream context is authoritative, stable, and you have no real
  disagreement with its shape — e.g. consuming a well-designed, versioned
  third-party API where you'd genuinely gain nothing by inventing your own
  parallel vocabulary for the exact same concept.
- **Separate Ways** — decide two contexts have no relationship worth
  building at all; duplicate the small amount of logic rather than
  integrating. Legitimate when the integration cost would exceed the
  duplication cost — the option this template *didn't* pick for
  `catalog`/`ordering`, since "what does this order cost" genuinely needs
  real catalog data.
- **Partnership** — two teams' contexts succeed or fail together, so they
  coordinate as equals on any shared interface change, with neither side
  "upstream." Same code shape as Customer–Supplier again; the difference
  is again about team relationship, not about anything import-linter can
  check.

**A caveat about enforcing any of this mechanically.** `pyproject.toml`'s
import-linter contracts for the `ordering`↔`catalog` relationship are
deliberately scoped to `domain`/`application`/`infrastructure`, not
`presentation` — both contexts' routers import the shared `app.containers`
composition root (for `Provide[Container...]`), and that root necessarily
imports *both* contexts to wire them. Left unscoped, that shared root would
show up as a transitive import path in both directions, and the contract
would flag it as if `ordering` depended on `catalog`'s internals even
though the actual domain/application code never touches it. Worth knowing
before trusting any import-linter contract's silence as a complete
guarantee — it checks the graph it's told to check, not "no relationship
exists anywhere in this codebase."

## Anti-Corruption Layer

An ACL is a translation boundary a *downstream* context puts around a
dependency on someone else's model, so that model's shape, quirks, and
future changes never leak past the boundary into the downstream context's
own domain. Without one, the moment it's more convenient to reuse the
upstream type directly than to maintain a translation, the two contexts'
models silently merge — and now a change in one breaks the other.

This template's ACL is `ordering/infrastructure/catalog_acl.py`'s
`CatalogAntiCorruptionLayer`. Trace the seam:

1. `ordering/application/ports/book_catalog.py` declares `BookCatalog`, a
   `Protocol` returning `ordering`'s own `OrderedBookSnapshot` — `ordering`'s
   domain and application code only ever import *this*, never anything
   from `catalog`.
2. `CatalogAntiCorruptionLayer` implements `BookCatalog`. Its constructor
   takes `catalog.published.lookup.CatalogLookup` — this class, and only
   this class, in the entire `ordering` package, imports anything from
   `app.contexts.catalog`.
3. `find()` calls the upstream interface, gets back `catalog`'s
   `CatalogBookSummary`, and returns `ordering`'s own `OrderedBookSnapshot`
   built from it. That's the whole translation.
4. `containers.py` wires `catalog_acl = providers.Factory(
   CatalogAntiCorruptionLayer, catalog_lookup=catalog_lookup)` and injects
   it into `place_order_use_case` as `catalog=catalog_acl`. The composition
   root — not either context's own code — is the one place allowed to
   introduce two contexts to each other.

**What it buys, concretely, and how to see it:**

- `tests/application/ordering/test_place_order.py` tests `PlaceOrderUseCase`
  against `FakeBookCatalog` — a fake that has never heard of `catalog` — and
  never imports `app.contexts.catalog`. Grep it; the import isn't there.
- `tests/application/ordering/test_place_order.py::
  test_a_later_catalog_price_change_does_not_affect_an_existing_order` and
  its real-database counterpart in `tests/e2e/ordering/test_orders_api.py`
  both prove the actual payoff: because `OrderLine` stores a
  `OrderedBookSnapshot` — data copied out through the ACL at order time,
  not a live reference — changing a book's price in `catalog` after an
  order is placed cannot retroactively change that order's total. Try
  deleting the ACL and having `PlaceOrderUseCase` hold onto a `catalog.Book`
  directly instead, and this property disappears: you'd either need to
  re-fetch and re-price every historical order's lines on demand (wrong —
  history should not move under you) or accept that `ordering` now has a
  hard dependency on `catalog`'s exact aggregate shape (wrong — see
  [Bounded Context](#bounded-context)).
- `tests/integration/ordering/test_catalog_acl.py` exercises the *real* ACL
  against a real `SqlAlchemyCatalogLookup` and a real database — no fakes on
  either side — proving the translation itself, not just the port shape.

**When you don't need one:** if a "foreign" model is already exactly the
shape you want and you have no reason to expect it to diverge from your
needs, an ACL is pure ceremony — see Conformist, above.

## Open Host Service & Published Language

Covered in detail under [Context Map](#context-map); the short version:
`catalog/published/` is `catalog`'s explicit, minimal, stable public
interface for other contexts (the Open Host Service), and
`CatalogBookSummary` is the data shape it promises to keep working (the
Published Language). It's a *separate* type from `catalog`'s own internal
`BookReadModel` (`application/read_models.py`) on purpose, even though they
currently look almost identical: `BookReadModel` can change the moment
catalog's own screens need it to; `CatalogBookSummary` changing is a
cross-context breaking change, and keeping them as two types is what makes
that distinction visible in the code instead of just in someone's head.

`published/` sits as a top-level sibling of `domain/`, `application/`,
`infrastructure/`, and `presentation/` inside `catalog/` specifically so
the import-linter contract that governs it stays simple: everything except
`catalog.published` is off-limits to `ordering`. Nothing inside `catalog`
itself is expected to import `published/` either — it exists only for
consumers on the other side of the context boundary.

## Aggregate

An aggregate is a cluster of objects (entities and value objects) treated
as one consistency boundary, with one member — the aggregate root — as the
only entry point from outside. `Book` (`catalog/domain/book.py`) is a
single-entity aggregate. `Order` (`ordering/domain/order.py`) is a richer
example: the root, plus a collection of `OrderLine` value objects, with
`Order.total_cents` and the "at least one line" invariant enforced at the
aggregate level, not per-line.

**The rule this template follows that's easy to violate by accident:
an aggregate references other aggregates by identity or by copied data,
never by holding a live object reference.** `Order` doesn't hold a `Book`;
it holds an `OrderedBookSnapshot` — a value object copied out via the ACL
at order-placement time (see [Anti-Corruption
Layer](#anti-corruption-layer)). This is what keeps `Order`'s consistency
boundary from silently growing to include the entirety of `catalog` — if
`Order` held a live `Book`, "is this order still valid" would depend on
mutable state outside `Order`'s own boundary, and two aggregates would be
changing together without either one's repository knowing about the other.

## Entity vs. Value Object

An **entity** has identity that persists through change — two `Book`s with
the same `id` are the same book even if every other field differs
(`shared/domain/entity.py::AggregateRoot.__eq__` is identity-based, not
field-based; see `tests/unit/catalog/test_book_aggregate.py
::TestIdentityEquality` and its `ordering` counterpart in
`tests/unit/ordering/test_order_aggregate.py`). A **value object** has no
identity — it's defined entirely by its fields, is immutable, and two
instances with equal fields are simply equal, full stop.

Entities in this repo: `Book`, `Order` (via `BookId`/`OrderId`, both
`EntityId` subclasses in `shared/domain/identifier.py`). Value objects:
`Title`, `Isbn`, `Money` (catalog); `Quantity`, `OrderedBookSnapshot`,
`OrderLine` (ordering) — all frozen dataclasses that validate themselves in
`__post_init__` and raise a domain error rather than silently accepting bad
data.

**A subtlety that shows up at the persistence boundary:**
`ordering/infrastructure/persistence/models.py`'s `OrderLineRow` still has
a primary key (`id: Mapped[int]`, plain autoincrement) even though
`OrderLine` is a value object with no domain identity at all. That key is
purely a relational-storage technicality — a row has to exist as *a* row —
and `mappers.py` never reads it back into the domain model. Contrast
`BookRow.id`/`OrderRow.id`, which *are* real domain identifiers
(`book.id.value`/`order.id.value`) persisted as the primary key on purpose.
If you ever find a domain value object's technical surrogate key leaking
into a read model, a command, or anywhere else outside `infrastructure/`,
that's the tell that the entity/value-object line has been crossed by
accident.

## Domain Event

Something that happened, named in the past tense, that other parts of the
system might care about: `BookRegistered`, `BookPriceChanged`
(`catalog/domain/events.py`), `OrderPlaced` (`ordering/domain/events.py`).
`AggregateRoot.record_event()`/`pull_events()`
(`shared/domain/entity.py`) is the recording seam; a use case pulls an
aggregate's events after doing its work and publishes each one via
`shared/infrastructure/events.py::publish` (the one place a plain
dataclass event turns into something dispatched through abxbus).

This is in-memory and best-effort — see that module's docstring and the
README's "Growing this template" for the transactional outbox that would
make it reliable. Nothing about `ordering` changes that; `PlaceOrderUseCase`
publishes `OrderPlaced` exactly the way `RegisterBookUseCase` publishes
`BookRegistered`.

## Repository

One repository per aggregate, addressed by the aggregate's identity, never
returning a raw ORM row or another aggregate's internals. `BookRepository`/
`SqlAlchemyBookRepository` (catalog) and the newly-added `OrderRepository`/
`SqlAlchemyOrderRepository` (ordering) follow the same shape — both are
`Protocol` ports implemented by a class inheriting
`shared/infrastructure/database/session_scoped.py::SqlAlchemySessionScoped`,
proving that base class isn't catalog-specific. `SqlAlchemyOrderRepository`
also demonstrates loading a real one-to-many relationship
(`Order`→`OrderLine`, via `OrderRow`/`OrderLineRow`) through a repository,
which `catalog`'s single-table `Book` never needed to.

## Factory

In DDD, "Factory" usually means encapsulating complex construction and its
invariants at one clear entry point — not necessarily a separate object
implementing a `Factory` interface (that's the GoF pattern; DDD's usage is
broader). `Book.register()` and `Order.place()` are both factories in this
sense: classmethods that mint the aggregate's id, establish its initial
state, enforce the invariants that must hold the instant it exists (an
`Order` needs at least one line — `EmptyOrderError` if not), and record the
event marking that creation. Neither aggregate has a public constructor
path that skips this — there's exactly one way to bring each into
existence validly.

## Domain Service

Domain logic that doesn't naturally belong to any single entity or value
object — usually because it needs *more than one* aggregate, or doesn't
fit any one aggregate's own responsibility, to compute. Not implemented in
this template: nothing here currently needs one. A domain service would
look like a plain class (not a use case — no I/O, no repositories, no
transaction handling; just domain logic) taking the aggregates/values it
needs as arguments, e.g., sketched (not part of this codebase):

```python
class BulkDiscountPolicy:
    """Needs more than one Order to decide anything — doesn't belong on
    Order itself."""

    def applies_to(self, orders_this_month: Sequence[Order]) -> bool:
        return sum(o.total_cents for o in orders_this_month) > 100_00 * 100
```

The tell that you need one: you're about to add a method to an aggregate
that requires *another* aggregate (or a collection of them) as an argument,
and the logic doesn't conceptually belong to either one alone. Until that's
true, resist adding one speculatively — see `RegisterBooksBatchUseCase`
and `CatalogTransaction` for another example of this template adding a
pattern only once a concrete use case demonstrated the need for it (README,
"Design decisions worth knowing").

## Specification

A reusable, named, combinable predicate over a domain object — `is_satisfied_by(candidate) -> bool`, typically composable with `and`/`or`/`not`. Not implemented here — `BookQueryService.list()`'s `title_contains` parameter is a plain keyword argument, not a Specification object, because there's exactly one filter and no need to combine it with others. A sketch of the shape, for when a query grows enough filter combinations that plain keyword arguments stop being readable (not part of this codebase):

```python
class Specification[T](Protocol):
    def is_satisfied_by(self, candidate: T) -> bool: ...

@dataclass(frozen=True, slots=True)
class TitleContains:
    substring: str

    def is_satisfied_by(self, book: Book) -> bool:
        return self.substring.lower() in str(book.title).lower()
```

Worth it once you have several independent, combinable filter conditions
that keyword arguments would turn into a combinatorial mess of optional
parameters; overkill for one.

## CQRS (lite)

Commands and use cases mutate state and return only an identifier (or
nothing); queries and read models never mutate state and are free to
denormalize, join, and shape data however the screen needs. Both contexts
follow this: `RegisterBookCommand`/`RegisterBookUseCase` vs.
`GetBookQuery`/`BookQueryService`/`BookReadModel` in `catalog`;
`PlaceOrderCommand`/`PlaceOrderUseCase` vs.
`GetOrderQuery`/`OrderReadModel` in `ordering`. "Lite" because it's one
database and one model underneath, not physically separate read/write
stores — see `application/ports/book_query_service.py`'s docstring for why
even that much separation earns its keep (a list view can never
accidentally trigger a lazy load or run a write-side invariant, because it
never constructs the aggregate at all).

`ordering.GetOrderUseCase` is the one deliberate exception worth naming:
it fetches the `Order` aggregate directly through `OrderRepository` rather
than through a parallel query-service port, because there's no list view
yet to justify one — see that use case's docstring. Add a
`OrderQueryService` the same way `catalog` did if `ordering` grows one.

## Command/Query Bus

Not a DDD pattern by itself — a mediator sitting on top of CQRS — but it's
what routes are built against in this template, so it's documented here
alongside the concepts it composes.

A route depends on `CommandBus`/`QueryBus` (`shared/application/bus.py`)
and calls `bus.dispatch(SomeCommand(...))` — it doesn't import or inject
any specific use case class. Each use case declares what it handles right
on itself:

```python
@command_handler(RegisterBookCommand)
class RegisterBookUseCase:
    async def execute(self, command: RegisterBookCommand) -> BookId: ...
```

— mirroring NestJS's `@nestjs/cqrs` (`@CommandHandler(SomeCommand)` +
`implements ICommandHandler<SomeCommand>`). `containers.py` only lists
*instances* (`providers.List(register_book_use_case, ...)`); there is no
second place that re-states which command each one handles.

**Why not a hand-maintained `{command_type: handler}` dict instead?**
Earlier iterations of this exact mechanism tried that, and a version before
it that used a separate generic `build_handler_registry` helper — both
worked, but needed a second place (a builder function or a dict literal)
that repeated pairing information already implied by each use case's own
name and signature. The decorator collapses that: the pairing lives once,
on the handler.

**What's checked, and what isn't, and by what:**

- `bus.dispatch(RegisterBookCommand(...))` resolves to a real `BookId`
  under `mypy --strict`, not `Any` — verified with `reveal_type()` before
  wiring this in. `Command[R]`/`Query[R]` (`shared/application/messages
  .py`) carry the result type as a type parameter, and `dispatch`'s own
  generic signature (`dispatch[R](self, command: Command[R]) -> R`) is
  what puts it back at the call site, even though the bus's internal
  `dict[type, handler]` lookup is necessarily type-erased.
- `@command_handler(X)`/`@query_handler(X)` do **not** statically verify
  the decorated class actually implements `CommandHandler[X, R]` for the
  right `R` — confirmed empirically: a generic decorator factory can't
  express "constrain the decorated class against the type argument from
  an earlier call" precisely enough for current mypy (a `Protocol` with a
  generic `__call__` looked like the right tool; mypy rejects matching a
  plain function against it). What closes that gap is each use case
  explicitly inheriting its specific `CommandHandler[X, R]`/`QueryHandler
  [X, R]` — e.g. `class RegisterBookUseCase(CommandHandler
  [RegisterBookCommand, BookId]):` — the same enforced-conformance pattern
  every port in this template uses (`application/ports/*.py`): a wrong
  `execute` signature is a `mypy` error at the class's own definition, and
  a forgotten override raises `TypeError` at construction, both verified
  empirically. `CommandHandler`/`QueryHandler`'s `execute` is
  `@abstractmethod` specifically to make the second guarantee real. The
  one gotcha this approach has, if a port ever declares an abstract
  `@property` the way `CatalogTransaction.books` does: the implementation
  needs a *real* property, not a same-named plain instance attribute —
  `ABCMeta` computes abstractness from the class before any instance
  exists, so an attribute merely assigned in `__init__`/`__aenter__`
  doesn't satisfy it (verified empirically; see
  `SqlAlchemyCatalogTransaction`'s docstring for the fix).
- Forgetting the decorator entirely, or registering two handlers for the
  same command, both raise a clear `ValueError` — naming the class or the
  command type — the moment `CommandBus`/`QueryBus` is constructed, not a
  bare `KeyError` at request time. See `tests/unit/test_bus.py`.

**Commands and queries get exactly one handler; events don't.** A command
asks for one specific thing to happen and one result back — `CommandBus`
enforces "exactly one" as a real invariant (see above). A domain event
announces something already happened, and dispatching it (`shared
/infrastructure/events.py::publish`, via abxbus) fans out to *every*
subscriber, including zero of them; nobody publishing an event should have
to know or care how many things react to it.

**Why the buses are `providers.Factory`, not `providers.Singleton`, in
`containers.py`, even though that means every request rebuilds every
handler:** one of them —`RegisterBooksBatchUseCase` — holds a
`CatalogTransaction` bound to one open session for its one call (see
[Anti-Corruption Layer](#anti-corruption-layer)'s neighbor concepts and
`application/ports/transaction.py`). Making the bus a `Singleton` would
make that use case, and the one transaction object it holds, shared
forever across every request — two concurrent batch-registration requests
would then race on the same session. The other six handlers would be
perfectly safe to share; keeping all seven the same shape (`Factory`) is a
deliberate trade of a little repeated object construction (cheap — no I/O)
against not having six safe providers and one unsafe one that looks
identical in `containers.py`.
`OrderQueryService` the same way `catalog` has one, if and when `ordering`
grows a page that needs it.
