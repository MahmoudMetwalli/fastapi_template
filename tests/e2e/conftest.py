"""`httpx.AsyncClient` + `ASGITransport` + `asgi-lifespan`, not
`TestClient` — `TestClient` runs a sync portal that fights an already-
running event loop and an async engine. `asgi-lifespan`'s `LifespanManager`
is what actually runs `create_app()`'s lifespan under `ASGITransport`,
which otherwise never triggers it — without it, `init_resources()` would
never fire.
"""

from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from dependency_injector import providers
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.main import create_app
from app.settings import Settings


@pytest.fixture
async def app(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[FastAPI]:
    fastapi_app = create_app(settings)
    container = fastapi_app.state.container
    # `container.<provider>.override(...)`, not `app.dependency_overrides`
    # — the latter silently does nothing for anything injected via
    # `Provide[]`, since those are resolved by dependency-injector's
    # `@inject` wrapper rather than FastAPI's own dependency graph. This is
    # the single most common source of "my override isn't being applied".
    # Only `session_factory` needs overriding: `book_repository`,
    # `book_query_service`, `catalog_transaction`, and every use case are
    # all built *from* it, so overriding this one provider is enough for
    # the whole graph to use the test database.
    container.session_factory.override(providers.Object(session_factory))
    try:
        async with LifespanManager(fastapi_app):
            yield fastapi_app
    finally:
        container.reset_override()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
