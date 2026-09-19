from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.containers import Container
from app.router import api_router
from app.settings import Settings
from app.shared.presentation.error_handlers import register_error_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    container = Container()
    # No `mode=` kwarg here: `Configuration.from_pydantic()` hardcodes
    # `model_dump(mode="python")` internally and passing `mode=` as a kwarg
    # collides with that and raises `TypeError`, regardless of value — see
    # `settings.py`. `DatabaseSettings` handles the `PostgresDsn`-to-`str`
    # conversion itself via a `field_serializer`, so this needs no override.
    container.config.from_pydantic(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        # `init_resources()`/`shutdown_resources()` are declared
        # `-> Optional[Awaitable[None]]` in the dependency-injector stubs —
        # under `mypy --strict` a bare `await container.init_resources()`
        # does not type-check, so the result is guarded explicitly.
        init_result = container.init_resources()
        if init_result is not None:
            await init_result
        try:
            yield
        finally:
            shutdown_result = container.shutdown_resources()
            if shutdown_result is not None:
                await shutdown_result

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    # `app.state`, not `app.container` (fastapi-ddd-example's choice) —
    # `state` is Starlette's supported attribute bag; `container` is an
    # undeclared attribute that just happens to work.
    app.state.container = container
    app.include_router(api_router, prefix="/api/v1")
    register_error_handlers(app)
    return app


app = create_app()
