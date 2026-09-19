"""Value objects: immutable, validate themselves in `__post_init__`, and
raise `DomainError` subclasses — never bare `ValueError` and never a
Pydantic `ValidationError`. Pydantic v1's class-attribute-constraint style
(`class Isbn(ConStr): min_length=10`) doesn't even survive the move to v2 —
class-level constraints are simply not read by pydantic-core any more — so
there's no migration path to preserve here; `__post_init__` is not a
workaround, it's the intended shape for the domain layer.
"""

from dataclasses import dataclass

from app.contexts.catalog.domain.errors import (
    InvalidIsbnError,
    InvalidTitleError,
    PriceMustBePositiveError,
)


@dataclass(frozen=True, slots=True)
class Title:
    value: str

    def __post_init__(self) -> None:
        if not (1 <= len(self.value.strip()) <= 200):
            raise InvalidTitleError("must be between 1 and 200 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Isbn:
    """An ISBN-13, validated including its checksum digit."""

    value: str

    def __post_init__(self) -> None:
        digits = self.value.replace("-", "").replace(" ", "")
        if len(digits) != 13 or not digits.isdigit() or not self._checksum_valid(digits):
            raise InvalidIsbnError(self.value)
        object.__setattr__(self, "value", digits)

    @staticmethod
    def _checksum_valid(digits: str) -> bool:
        total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12]))
        check_digit = (10 - total % 10) % 10
        return check_digit == int(digits[12])

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Money:
    """An amount in whole cents, in a single implied currency. Extend with
    a `currency` field before this template backs a multi-currency
    context."""

    amount_cents: int

    def __post_init__(self) -> None:
        if self.amount_cents <= 0:
            raise PriceMustBePositiveError(self.amount_cents)

    def __str__(self) -> str:
        return f"{self.amount_cents / 100:.2f}"
