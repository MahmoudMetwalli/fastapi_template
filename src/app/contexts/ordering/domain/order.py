"""The `Order` aggregate. No SQLAlchemy import, no Pydantic import, no
FastAPI import, and — the point of this whole context — no `catalog`
import either. Enforced mechanically by import-linter's "Domain is
framework-free" and "Ordering may only depend on catalog's published
interface" contracts in pyproject.toml, not just by convention.
"""

from dataclasses import dataclass, field

from app.contexts.ordering.domain.errors import EmptyOrderError
from app.contexts.ordering.domain.events import OrderPlaced
from app.contexts.ordering.domain.value_objects import OrderLine
from app.shared.domain.entity import AggregateRoot
from app.shared.domain.identifier import EntityId


@dataclass(frozen=True, slots=True)
class OrderId(EntityId):
    pass


@dataclass(slots=True, eq=False, kw_only=True)
class Order(AggregateRoot):
    id: OrderId
    lines: list[OrderLine] = field(default_factory=list)

    @classmethod
    def place(cls, *, lines: list[OrderLine]) -> Order:
        """Factory: an `Order` with no lines is not a partially-built
        order, it's an invalid one — the invariant is enforced here, at
        the one place an `Order` can come into existence, not left to
        callers to remember."""
        if not lines:
            raise EmptyOrderError()
        order_id = OrderId.new()
        order = cls(id=order_id, lines=lines)
        order.record_event(OrderPlaced(order_id=order_id, total_cents=order.total_cents))
        return order

    @property
    def total_cents(self) -> int:
        return sum(line.subtotal_cents for line in self.lines)
