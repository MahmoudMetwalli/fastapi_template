"""The one DI container. `Container()` must only ever be constructed inside
`create_app()` (see `main.py`) — never at this module's top level. Wiring
(`WiringConfiguration(packages=[...])`) runs on instantiation and imports
every module under `app.contexts`, including `presentation/router.py`,
which imports `Container` from *this* module; instantiating here would
therefore be a genuine import cycle.

`book_repository`/`book_query_service` are `Factory`s, not per-request-
scoped anything: their `SessionStrategy` (`own_session_factory_strategy`)
is immutable and holds no per-call state (see `shared/infrastructure/
database/session_strategy.py`), so a fresh instance per resolution costs
nothing and there's never a shared, mutable object for concurrent requests
to race over. `catalog_transaction` is also a plain `Factory`, injected
directly (never `.provider`) into `register_books_batch_use_case` — that
use case is itself resolved fresh once per request, and needs exactly one
transaction for its one `execute()` call, so there's nothing for a
`.provider`-style "call me again" reference to buy here; see
`register_books_batch.py`'s docstring for why that was tried first.

`ordering`'s `place_order_use_case` depends on `catalog_acl`, not
`catalog_lookup` directly — this is where the two contexts' composition
roots meet: `catalog_lookup` (implementing `catalog.published.lookup
.CatalogLookup`) is `catalog`'s side of the boundary, `catalog_acl`
(implementing `ordering.application.ports.book_catalog.BookCatalog`) is
`ordering`'s side, and gluing the two together — the only place that's
ever allowed to happen — is this container, not either context's own code.
"""

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.contexts.catalog.application.use_cases.change_book_price import ChangeBookPriceUseCase
from app.contexts.catalog.application.use_cases.get_book import GetBookUseCase
from app.contexts.catalog.application.use_cases.list_books import ListBooksUseCase
from app.contexts.catalog.application.use_cases.register_book import RegisterBookUseCase
from app.contexts.catalog.application.use_cases.register_books_batch import (
    RegisterBooksBatchUseCase,
)
from app.contexts.catalog.infrastructure.persistence.book_query_service import (
    SqlAlchemyBookQueryService,
)
from app.contexts.catalog.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from app.contexts.catalog.infrastructure.persistence.catalog_lookup import SqlAlchemyCatalogLookup
from app.contexts.catalog.infrastructure.persistence.transaction import SqlAlchemyCatalogTransaction
from app.contexts.ordering.application.use_cases.get_order import GetOrderUseCase
from app.contexts.ordering.application.use_cases.place_order import PlaceOrderUseCase
from app.contexts.ordering.infrastructure.catalog_acl import CatalogAntiCorruptionLayer
from app.contexts.ordering.infrastructure.persistence.order_repository import (
    SqlAlchemyOrderRepository,
)
from app.shared.infrastructure.database.engine import EngineResource
from app.shared.infrastructure.database.session_strategy import OwnSessionFactory
from app.shared.infrastructure.events import EventBusResource


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app.contexts"])

    config = providers.Configuration()

    engine = providers.Resource(
        EngineResource,
        dsn=config.database.dsn,
        echo=config.database.echo,
        pool_size=config.database.pool_size,
        max_overflow=config.database.max_overflow,
        pool_pre_ping=config.database.pool_pre_ping,
    )

    event_bus = providers.Resource(EventBusResource)

    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    own_session_factory_strategy = providers.Singleton(
        OwnSessionFactory, session_factory=session_factory
    )

    book_repository = providers.Factory(
        SqlAlchemyBookRepository, strategy=own_session_factory_strategy
    )
    book_query_service = providers.Factory(
        SqlAlchemyBookQueryService, strategy=own_session_factory_strategy
    )

    catalog_transaction = providers.Factory(
        SqlAlchemyCatalogTransaction, session_factory=session_factory
    )

    register_book_use_case = providers.Factory(
        RegisterBookUseCase, books=book_repository, event_bus=event_bus
    )
    change_book_price_use_case = providers.Factory(
        ChangeBookPriceUseCase, books=book_repository, event_bus=event_bus
    )
    get_book_use_case = providers.Factory(GetBookUseCase, book_queries=book_query_service)
    list_books_use_case = providers.Factory(ListBooksUseCase, book_queries=book_query_service)
    register_books_batch_use_case = providers.Factory(
        RegisterBooksBatchUseCase,
        transaction=catalog_transaction,
        event_bus=event_bus,
    )

    # catalog's published interface — the only part of `catalog` the
    # `ordering` context (below) is allowed to depend on.
    catalog_lookup = providers.Factory(
        SqlAlchemyCatalogLookup, strategy=own_session_factory_strategy
    )

    order_repository = providers.Factory(
        SqlAlchemyOrderRepository, strategy=own_session_factory_strategy
    )
    catalog_acl = providers.Factory(CatalogAntiCorruptionLayer, catalog_lookup=catalog_lookup)

    place_order_use_case = providers.Factory(
        PlaceOrderUseCase,
        orders=order_repository,
        catalog=catalog_acl,
        event_bus=event_bus,
    )
    get_order_use_case = providers.Factory(GetOrderUseCase, orders=order_repository)
