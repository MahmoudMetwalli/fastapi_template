"""The single place `DomainError`s become HTTP responses.

Both reference repos handle errors per-route instead: `fastapi-ddd-example`
catches three named exception types in every route function, and
`fastapi-todo-ddd` wraps every use case call in a bare
`except Exception: raise HTTPException(500)`, which silently turns every
domain error (not-found, invariant violation, conflict) into an opaque 500.
Registering handlers here means routes never need a try/except at all — see
`contexts/catalog/presentation/router.py`.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.shared.domain.errors import (
    ConflictError,
    DomainError,
    EntityNotFoundError,
    InvariantViolationError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(EntityNotFoundError)
    async def handle_not_found(_request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return _problem(status.HTTP_404_NOT_FOUND, exc)

    @app.exception_handler(InvariantViolationError)
    async def handle_invariant_violation(
        _request: Request, exc: InvariantViolationError
    ) -> JSONResponse:
        return _problem(status.HTTP_422_UNPROCESSABLE_ENTITY, exc)

    @app.exception_handler(ConflictError)
    async def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
        return _problem(status.HTTP_409_CONFLICT, exc)

    @app.exception_handler(DomainError)
    async def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        # Catch-all for a DomainError subclass that doesn't get a specific
        # mapping above yet — 400 rather than an opaque 500, and still
        # something a caller can act on.
        return _problem(status.HTTP_400_BAD_REQUEST, exc)


def _problem(status_code: int, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"detail": str(exc), "type": type(exc).__name__}
    )
