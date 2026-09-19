"""Same conventions as `catalog/presentation/router.py`: `@inject` is the
innermost decorator, `DomainError` subclasses propagate straight to the
handlers in `shared/presentation/error_handlers.py` — no try/except here,
including for `BookNotFoundInCatalogError`, which the Anti-Corruption
Layer's absence-as-`None` turns into a domain error one layer up, in
`PlaceOrderUseCase` — and routes depend on `CommandBus`/`QueryBus`
(`shared/application/bus.py`) rather than a specific use case class.
"""

from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.containers import Container
from app.contexts.ordering.application.commands import PlaceOrderCommand, PlaceOrderItem
from app.contexts.ordering.application.queries import GetOrderQuery
from app.contexts.ordering.presentation.schemas import (
    OrderCreatedResponse,
    OrderResponse,
    PlaceOrderRequest,
)
from app.shared.application.bus import CommandBus, QueryBus

router = APIRouter(prefix="/orders", tags=["ordering"])

Commands = Annotated[CommandBus, Depends(Provide[Container.command_bus])]
Queries = Annotated[QueryBus, Depends(Provide[Container.query_bus])]


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def place_order(payload: PlaceOrderRequest, bus: Commands) -> OrderCreatedResponse:
    order_id = await bus.dispatch(
        PlaceOrderCommand(
            items=[
                PlaceOrderItem(book_id=item.book_id, quantity=item.quantity)
                for item in payload.items
            ]
        )
    )
    return OrderCreatedResponse(id=order_id.value)


@router.get("/{order_id}")
@inject
async def get_order(order_id: UUID, bus: Queries) -> OrderResponse:
    read_model = await bus.dispatch(GetOrderQuery(order_id=order_id))
    return OrderResponse.model_validate(read_model)
