"""Application configuration.

`Settings` must never be instantiated at import time (module scope). Doing so
makes the importing module unusable without a fully populated environment,
which is exactly what breaks unit tests and `python -c "import app.main"`
sanity checks. Always construct it explicitly inside `create_app()`.
"""

from typing import Literal

from pydantic import BaseModel, PostgresDsn, field_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    # PostgresDsn (not `str`) so a malformed DATABASE__DSN fails fast at
    # startup with a clear validation error instead of a confusing asyncpg
    # connection failure. The tradeoff: `model_dump()` would otherwise
    # return the `PostgresDsn` object itself, not a string — verified
    # empirically, since `dependency_injector.providers.Configuration
    # .from_pydantic()` hardcodes `settings.model_dump(mode="python")`
    # internally (`providers.pyx`) and does NOT accept a `mode` override
    # (passing `mode=...` as a kwarg collides with that hardcoded keyword
    # and raises `TypeError: got multiple values for keyword argument
    # 'mode'`, regardless of the value passed). `create_async_engine`
    # cannot consume that object directly, so the field is serialized to a
    # plain `str` unconditionally here instead.
    dsn: PostgresDsn
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True

    @field_serializer("dsn")
    def _serialize_dsn(self, value: PostgresDsn) -> str:
        return str(value)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "fastapi-ddd-template"
    environment: Literal["local", "test", "production"] = "local"
    debug: bool = False
    database: DatabaseSettings
