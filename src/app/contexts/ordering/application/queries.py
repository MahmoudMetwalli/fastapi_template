from dataclasses import dataclass
from uuid import UUID

from app.contexts.ordering.application.read_models import OrderReadModel
from app.shared.application.messages import Query


@dataclass(frozen=True, slots=True, kw_only=True)
class GetOrderQuery(Query[OrderReadModel]):
    order_id: UUID
