from app.shared.domain.errors import EntityNotFoundError, InvariantViolationError


class OrderNotFoundError(EntityNotFoundError):
    def __init__(self, order_id: object) -> None:
        super().__init__(f"Order {order_id} was not found")


class EmptyOrderError(InvariantViolationError):
    def __init__(self) -> None:
        super().__init__("An order must contain at least one line")


class QuantityMustBePositiveError(InvariantViolationError):
    def __init__(self, quantity: int) -> None:
        super().__init__(f"Quantity must be positive, got {quantity}")


class BookNotFoundInCatalogError(InvariantViolationError):
    """Raised by `PlaceOrderUseCase`, not by the Anti-Corruption Layer
    itself — `BookCatalog.find()` (the port the ACL implements) just
    returns `None`, the same "not found is a value, not an exception"
    convention every other port in this template follows. Deciding that a
    missing book is an error is the use case's call, not the port's."""

    def __init__(self, book_id: object) -> None:
        super().__init__(f"Book {book_id} was not found in the catalog")
