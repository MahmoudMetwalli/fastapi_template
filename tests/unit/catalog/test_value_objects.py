"""No fixtures, no IO, no event loop — this is the tier the
stdlib-dataclass-over-Pydantic decision buys: `python -m pytest
tests/unit` needs nothing installed beyond the domain module itself.
"""

import pytest

from app.contexts.catalog.domain.errors import (
    InvalidIsbnError,
    InvalidTitleError,
    PriceMustBePositiveError,
)
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title


class TestTitle:
    def test_accepts_a_normal_title(self) -> None:
        assert str(Title("Domain-Driven Design")) == "Domain-Driven Design"

    def test_rejects_an_empty_title(self) -> None:
        with pytest.raises(InvalidTitleError):
            Title("   ")

    def test_rejects_a_title_over_200_characters(self) -> None:
        with pytest.raises(InvalidTitleError):
            Title("x" * 201)


class TestIsbn:
    def test_accepts_a_valid_isbn_13(self) -> None:
        assert str(Isbn("9780321125217")) == "9780321125217"

    def test_normalizes_hyphens_and_spaces(self) -> None:
        assert str(Isbn("978-0-321-12521-7")) == "9780321125217"

    def test_rejects_a_bad_checksum_digit(self) -> None:
        with pytest.raises(InvalidIsbnError):
            Isbn("9780321125218")

    def test_rejects_the_wrong_length(self) -> None:
        with pytest.raises(InvalidIsbnError):
            Isbn("12345")

    def test_rejects_non_digit_characters(self) -> None:
        with pytest.raises(InvalidIsbnError):
            Isbn("97803211252XX")


class TestMoney:
    def test_accepts_a_positive_amount(self) -> None:
        assert Money(4999).amount_cents == 4999

    def test_rejects_zero(self) -> None:
        with pytest.raises(PriceMustBePositiveError):
            Money(0)

    def test_rejects_a_negative_amount(self) -> None:
        with pytest.raises(PriceMustBePositiveError):
            Money(-100)
