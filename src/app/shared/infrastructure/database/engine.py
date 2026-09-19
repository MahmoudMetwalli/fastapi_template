"""The async engine resource, kept out of `containers.py` so the container
stays a pure wiring/composition file — see `shared/infrastructure/events.py`
for the same pattern applied to the event bus.
"""

from dependency_injector import resources
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class EngineResource(resources.AsyncResource[AsyncEngine]):
    """A `dependency_injector.resources.AsyncResource` subclass — the
    library's own class-based idiom for a resource with init/shutdown
    (`init()`/`shutdown()`, not `__init__`; the base class already defines
    `__init__` to store the constructor args/kwargs that `init()` receives)
    — rather than a bare async-generator function wrapped in try/finally.
    """

    async def init(
        self, dsn: str, echo: bool, pool_size: int, max_overflow: int, pool_pre_ping: bool
    ) -> AsyncEngine:
        return create_async_engine(
            dsn,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
        )

    async def shutdown(self, resource: AsyncEngine | None) -> None:
        if resource is not None:
            await resource.dispose()
