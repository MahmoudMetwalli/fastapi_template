"""Import every context's ORM models so `Base.metadata` is complete.

This is the one file that stands in for the reference repos' global
`persistence/` package (see the project plan's decision #1). Alembic's
`env.py` imports this module before generating a revision. Forgetting to add
a new context here produces a loud, empty `alembic revision --autogenerate`
rather than silent schema drift — that tradeoff (one line to remember, vs.
tables missing from migrations) is why this file exists at all instead of
relying on package auto-discovery.

Add one import per context as it's created:
"""

from app.contexts.catalog.infrastructure.persistence import models as _catalog_models  # noqa: F401
from app.contexts.ordering.infrastructure.persistence import (
    models as _ordering_models,  # noqa: F401
)
