"""The Published Language: the vocabulary `catalog` exposes to *other*
bounded contexts. Kept separate from `application/read_models.py` — which
is catalog's own, internal read-side output for catalog's own screens —
even though the two currently look similar. They're allowed to drift
apart: a read model can change freely alongside catalog's own UI; this one
is a promise to every other context that depends on it, and changing its
shape is a cross-context breaking change, not a local refactor.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogBookSummary:
    """Everything an outside context is allowed to know about a book: its
    id, title, and current price. Deliberately smaller than the `Book`
    aggregate (no ISBN, no lifecycle) — the published surface should only
    ever grow on actual demand from a consumer, never speculatively."""

    id: UUID
    title: str
    price_cents: int
