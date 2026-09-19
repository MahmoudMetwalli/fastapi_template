import pytest

from app.contexts.ordering.domain.errors import EmptyOrderError
from app.contexts.ordering.domain.events import OrderPlaced
from app.contexts.ordering.domain.order import Order
from app.contexts.ordering.domain.value_objects import OrderLine, Quantity
from tests.factories import make_ordered_book_snapshot


def _line(*, unit_price_cents: int = 999, quantity: int = 1) -> OrderLine:
    return OrderLine(
        snapshot=make_ordered_book_snapshot(unit_price_cents=unit_price_cents),
        quantity=Quantity(quantity),
    )


class TestPlace:
    def test_mints_an_id(self) -> None:
        order = Order.place(lines=[_line()])
        assert order.id is not None

    def test_rejects_an_empty_order(self) -> None:
        with pytest.raises(EmptyOrderError):
            Order.place(lines=[])

    def test_records_an_order_placed_event_with_the_total(self) -> None:
        order = Order.place(
            lines=[
                _line(unit_price_cents=500, quantity=2),
                _line(unit_price_cents=100, quantity=1),
            ]
        )

        events = order.pull_events()

        assert len(events) == 1
        assert isinstance(events[0], OrderPlaced)
        assert events[0].order_id == order.id
        assert events[0].total_cents == 1100

    def test_total_cents_sums_every_line(self) -> None:
        order = Order.place(
            lines=[
                _line(unit_price_cents=500, quantity=2),
                _line(unit_price_cents=100, quantity=3),
            ]
        )
        assert order.total_cents == 1300


class TestIdentityEquality:
    def test_two_orders_with_the_same_id_are_equal_even_if_lines_differ(self) -> None:
        order = Order.place(lines=[_line()])
        same_id_different_lines = Order(id=order.id, lines=[_line(unit_price_cents=1)])
        assert order == same_id_different_lines
