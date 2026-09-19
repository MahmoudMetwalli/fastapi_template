import pytest

from app.contexts.ordering.domain.errors import QuantityMustBePositiveError
from app.contexts.ordering.domain.value_objects import OrderLine, Quantity
from tests.factories import make_ordered_book_snapshot


class TestQuantity:
    def test_rejects_zero(self) -> None:
        with pytest.raises(QuantityMustBePositiveError):
            Quantity(0)

    def test_rejects_negative(self) -> None:
        with pytest.raises(QuantityMustBePositiveError):
            Quantity(-1)


class TestOrderLine:
    def test_subtotal_is_unit_price_times_quantity(self) -> None:
        line = OrderLine(
            snapshot=make_ordered_book_snapshot(unit_price_cents=500), quantity=Quantity(3)
        )
        assert line.subtotal_cents == 1500
