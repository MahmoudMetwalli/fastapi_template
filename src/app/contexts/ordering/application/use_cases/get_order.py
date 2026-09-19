"""Read path: fetches the aggregate directly through `OrderRepository`,
unlike `catalog`'s `GetBookUseCase` (which goes through a separate
`BookQueryService`). `Order` is a small aggregate fetched one at a time —
there's no list view here yet to justify a parallel read-side port; add
one the same way `catalog` did (see its `application/ports/
book_query_service.py`) if `ordering` grows one.
"""

from app.contexts.ordering.application.ports.order_repository import OrderRepository
from app.contexts.ordering.application.queries import GetOrderQuery
from app.contexts.ordering.application.read_models import OrderLineReadModel, OrderReadModel
from app.contexts.ordering.domain.errors import OrderNotFoundError
from app.contexts.ordering.domain.order import OrderId
from app.shared.application.bus import query_handler
from app.shared.application.messages import QueryHandler


@query_handler(GetOrderQuery)
class GetOrderUseCase(QueryHandler[GetOrderQuery, OrderReadModel]):
    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    async def execute(self, query: GetOrderQuery) -> OrderReadModel:
        order = await self._orders.get(OrderId(query.order_id))
        if order is None:
            raise OrderNotFoundError(query.order_id)
        return OrderReadModel(
            id=order.id.value,
            total_cents=order.total_cents,
            lines=[
                OrderLineReadModel(
                    book_id=line.snapshot.book_id,
                    title=line.snapshot.title,
                    unit_price_cents=line.snapshot.unit_price_cents,
                    quantity=line.quantity.value,
                    subtotal_cents=line.subtotal_cents,
                )
                for line in order.lines
            ],
        )
