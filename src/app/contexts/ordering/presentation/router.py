"""Same conventions as `catalog/presentation/router.py`: `@inject` is the
innermost decorator, and `DomainError` subclasses propagate straight to
the handlers in `shared/presentation/error_handlers.py` — no try/except
here, including for `BookNotFoundInCatalogError`, which the Anti-Corruption
Layer's absence-as-`None` turns into a domain error one layer up, in
`PlaceOrderUseCase`.
"""

from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.containers import Container
from app.contexts.ordering.application.commands import PlaceOrderCommand, PlaceOrderItem
from app.contexts.ordering.application.queries import GetOrderQuery
from app.contexts.ordering.application.use_cases.get_order import GetOrderUseCase
from app.contexts.ordering.application.use_cases.place_order import PlaceOrderUseCase
from app.contexts.ordering.presentation.schemas import (
    OrderCreatedResponse,
    OrderResponse,
    PlaceOrderRequest,
)

router = APIRouter(prefix="/orders", tags=["ordering"])

PlaceOrderUC = Annotated[PlaceOrderUseCase, Depends(Provide[Container.place_order_use_case])]
GetOrderUC = Annotated[GetOrderUseCase, Depends(Provide[Container.get_order_use_case])]


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def place_order(payload: PlaceOrderRequest, use_case: PlaceOrderUC) -> OrderCreatedResponse:
    order_id = await use_case.execute(
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
async def get_order(order_id: UUID, use_case: GetOrderUC) -> OrderResponse:
    read_model = await use_case.execute(GetOrderQuery(order_id=order_id))
    return OrderResponse.model_validate(read_model)
