"""The safety net for the two typing gaps documented in the project plan's
"Getting strict typing out of dependency-injector": `Factory.__init__`
types every injected kwarg as `Any`, and `Provide[...]` isn't in the stubs
at all, so a renamed constructor parameter or a provider pointed at the
wrong name would pass mypy silently. Resolving the real graph here catches
both — and needs no live database, because `create_async_engine` doesn't
connect eagerly; it only builds a connection pool.

Whether a provider's `__call__` returns the object directly or an
awaitable of it is not uniform across providers, verified empirically:
anything built (even indirectly) from `session_factory`/`event_bus` needs
awaiting, since both ultimately depend on `Resource` providers.
`inspect.isawaitable` below handles both.
"""

import inspect

from app.containers import Container
from app.settings import DatabaseSettings, Settings


def _settings() -> Settings:
    return Settings(
        database=DatabaseSettings(dsn="postgresql+asyncpg://app:app@localhost:5432/app")
    )


async def _resolve[T](value: T) -> T:
    return await value if inspect.isawaitable(value) else value


class TestContainer:
    def test_check_dependencies_does_not_raise(self) -> None:
        """Catches an undefined `Dependency` provider — a provider
        referenced but never declared on the container."""
        container = Container()
        container.config.from_pydantic(_settings())

        container.check_dependencies()

    async def test_resolves_every_provider_without_a_live_database(self) -> None:
        container = Container()
        container.config.from_pydantic(_settings())

        try:
            assert await _resolve(container.own_session_factory_strategy()) is not None
            assert await _resolve(container.book_repository()) is not None
            assert await _resolve(container.book_query_service()) is not None
            assert await _resolve(container.catalog_transaction()) is not None
            assert await _resolve(container.register_book_use_case()) is not None
            assert await _resolve(container.change_book_price_use_case()) is not None
            assert await _resolve(container.get_book_use_case()) is not None
            assert await _resolve(container.list_books_use_case()) is not None
            assert await _resolve(container.register_books_batch_use_case()) is not None
            assert await _resolve(container.catalog_lookup()) is not None
            assert await _resolve(container.order_repository()) is not None
            assert await _resolve(container.catalog_acl()) is not None
            assert await _resolve(container.place_order_use_case()) is not None
            assert await _resolve(container.get_order_use_case()) is not None
            assert await _resolve(container.command_bus()) is not None
            assert await _resolve(container.query_bus()) is not None
        finally:
            shutdown_result = container.shutdown_resources()
            if shutdown_result is not None:
                await shutdown_result
