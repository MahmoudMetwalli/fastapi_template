"""A reusable base for infrastructure classes (repositories, query
services) that need a `SessionStrategy` (see `session_strategy.py`) but
shouldn't each redeclare the same one-line constructor. Every context's
repository/query-service classes should inherit this instead of writing
`def __init__(self, strategy: SessionStrategy) -> None: self._strategy = strategy`
themselves — subclasses use `self._strategy.session()` directly wherever
they need a session; that call already returns a usable async context
manager, so there's nothing this base class needs to wrap it in.
"""

from app.shared.infrastructure.database.session_strategy import SessionStrategy


class SqlAlchemySessionScoped:
    def __init__(self, strategy: SessionStrategy) -> None:
        self._strategy = strategy
