from app.shared.domain.errors import ConflictError, EntityNotFoundError, InvariantViolationError


class BookNotFoundError(EntityNotFoundError):
    def __init__(self, book_id: object) -> None:
        super().__init__(f"Book {book_id} was not found")


class InvalidIsbnError(InvariantViolationError):
    def __init__(self, isbn: str) -> None:
        super().__init__(f"'{isbn}' is not a valid ISBN-13")


class InvalidTitleError(InvariantViolationError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid book title: {reason}")


class PriceMustBePositiveError(InvariantViolationError):
    def __init__(self, amount_cents: int) -> None:
        super().__init__(f"Price must be positive, got {amount_cents} cents")


class DuplicateIsbnError(ConflictError):
    def __init__(self, isbn: str) -> None:
        super().__init__(f"A book with ISBN '{isbn}' already exists")
