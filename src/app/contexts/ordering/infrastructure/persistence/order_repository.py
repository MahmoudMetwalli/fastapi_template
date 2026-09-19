"""`SqlAlchemyOrderRepository` inherits its `SessionStrategy` from
`SqlAlchemySessionScoped` (`shared/infrastructure/database/`), exactly
like `catalog`'s repositories — proof that base class isn't
`catalog`-specific.
"""

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.contexts.ordering.application.ports.order_repository import OrderRepository
from app.contexts.ordering.domain.order import Order, OrderId
from app.contexts.ordering.infrastructure.persistence.mappers import to_domain, to_row
from app.contexts.ordering.infrastructure.persistence.models import OrderRow
from app.shared.infrastructure.database.session_scoped import SqlAlchemySessionScoped


class SqlAlchemyOrderRepository(SqlAlchemySessionScoped):
    async def get(self, order_id: OrderId) -> Order | None:
        # `selectinload`, not `session.get`: the default `OwnSessionFactory`
        # strategy closes this session at the end of this `async with`
        # block, so `order.lines` must already be loaded before then — a
        # lazy load after the session closes would raise `MissingGreenlet`.
        statement = (
            select(OrderRow)
            .where(OrderRow.id == order_id.value)
            .options(selectinload(OrderRow.lines))
        )
        async with self._strategy.session() as session:
            result = await session.execute(statement)
            row = result.scalar_one_or_none()
            return to_domain(row) if row is not None else None

    async def add(self, order: Order) -> None:
        async with self._strategy.session() as session:
            session.add(to_row(order))


if TYPE_CHECKING:
    _conforms_to_order_repository: type[OrderRepository] = SqlAlchemyOrderRepository
