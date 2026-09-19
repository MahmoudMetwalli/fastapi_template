"""Root fixtures shared by the integration and e2e tiers.

Unit and application tests (see `tests/unit/`, `tests/application/`) need
none of this — that's the point of the split. This file only provides what
a real database is needed for.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.postgres import PostgresContainer

from app.settings import DatabaseSettings, Settings

_REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Points at `TEST_DATABASE_URL` if set (e.g. a service container in
    CI), otherwise spins up a throwaway Postgres via testcontainers."""
    dsn = os.environ.get("TEST_DATABASE_URL")
    if dsn is None:
        container = PostgresContainer("postgres:17-alpine", driver="asyncpg")
        container.start()
        dsn = container.get_connection_url()

    return Settings(database=DatabaseSettings(dsn=dsn))


@pytest.fixture(scope="session")
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    """Runs real Alembic migrations against the throwaway database, not
    `Base.metadata.create_all()` — this exercises the migrations on every
    test run and makes model/migration drift impossible. Both reference
    repos use `create_all` at startup and neither ships a migration at
    all.
    """
    alembic_cfg = Config(_REPO_ROOT / "alembic.ini")
    alembic_cfg.set_main_option("script_location", str(_REPO_ROOT / "migrations"))
    # Alembic's own env.py builds its own Settings()/engine from env vars;
    # point it at the same throwaway database via the environment rather
    # than threading the DSN through `alembic_cfg`.
    os.environ["DATABASE__DSN"] = str(settings.database.dsn)
    # `command.upgrade` runs the *async* migration template's `env.py`,
    # which calls `asyncio.run(...)` internally — that raises
    # "asyncio.run() cannot be called from a running event loop" here,
    # since this fixture is itself already running inside pytest-asyncio's
    # loop. Running it in a worker thread gives it a thread with no
    # running loop of its own, which is all `asyncio.run()` needs.
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    db_engine = create_async_engine(str(settings.database.dsn))
    try:
        yield db_engine
    finally:
        await db_engine.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Function-scoped and savepoint-isolated: every session this hands
    out is bound to the *same* connection and its one outer transaction,
    which is rolled back after the test — but code under test can still
    call a real `commit()`/`.begin()`, because
    `join_transaction_mode="create_savepoint"` turns that into releasing a
    savepoint rather than ending the outer transaction. Since
    `SqlAlchemyBookRepository` opens a session per method call (see
    `infrastructure/persistence/book_repository.py`), a real
    `async_sessionmaker` is enough here — no custom stand-in needed, for
    either the integration or the e2e tier (see `tests/e2e/conftest.py`).
    """
    async with engine.connect() as connection:
        outer_transaction = await connection.begin()
        yield async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        )
        await outer_transaction.rollback()
