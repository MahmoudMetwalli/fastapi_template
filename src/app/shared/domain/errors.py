"""Framework-free domain error hierarchy.

These are plain exceptions — never `HTTPException` subclasses. Coupling the
domain to Starlette/FastAPI (as `fastapi-ddd-example`'s
`common/errors/exception.py` does) makes the domain untestable without the
web framework installed, and pins every error to one transport.

`app/shared/presentation/error_handlers.py` is the single place these get
translated into HTTP responses.
"""


class DomainError(Exception):
    """Base class for all domain errors."""


class InvariantViolationError(DomainError):
    """A domain rule / invariant was violated (bad input to a VO or entity)."""


class EntityNotFoundError(DomainError):
    """A referenced entity does not exist."""


class ConflictError(DomainError):
    """The operation conflicts with existing state (e.g. a uniqueness rule)."""
