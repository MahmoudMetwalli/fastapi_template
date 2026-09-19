"""The one application-layer test suite that actually exercises atomicity
across multiple repository calls — see
`application/ports/transaction.py` for why this use case is the exception
to "every repository call is its own transaction."
"""

import pytest
from abxbus import EventBus

from app.contexts.catalog.application.commands import (
    RegisterBookBatchItem,
    RegisterBooksBatchCommand,
)
from app.contexts.catalog.application.use_cases.register_books_batch import (
    RegisterBooksBatchUseCase,
)
from app.contexts.catalog.domain.errors import DuplicateIsbnError
from app.contexts.catalog.domain.events import BookRegistered
from tests.factories import make_book, make_isbn
from tests.fakes import FakeCatalogTransaction, InMemoryBookRepository


@pytest.fixture
def repository() -> InMemoryBookRepository:
    return InMemoryBookRepository()


@pytest.fixture
def transaction(repository: InMemoryBookRepository) -> FakeCatalogTransaction:
    return FakeCatalogTransaction(repository)


class TestRegisterBooksBatch:
    async def test_registers_every_book_in_the_batch(
        self,
        repository: InMemoryBookRepository,
        transaction: FakeCatalogTransaction,
        event_bus: EventBus,
        received_events: list[object],
    ) -> None:
        use_case = RegisterBooksBatchUseCase(transaction=transaction, event_bus=event_bus)
        items = [
            RegisterBookBatchItem(
                title="Domain-Driven Design", isbn=make_isbn(1), price_cents=4999
            ),
            RegisterBookBatchItem(title="Clean Architecture", isbn=make_isbn(2), price_cents=3499),
        ]

        book_ids = await use_case.execute(RegisterBooksBatchCommand(items=items))

        assert len(book_ids) == 2
        assert len(repository.books) == 2
        assert len(received_events) == 2
        assert all(isinstance(event, BookRegistered) for event in received_events)

    async def test_rolls_back_the_whole_batch_when_one_item_duplicates_an_existing_isbn(
        self,
        repository: InMemoryBookRepository,
        transaction: FakeCatalogTransaction,
        event_bus: EventBus,
        received_events: list[object],
    ) -> None:
        existing = make_book(isbn=make_isbn(10))
        await repository.add(existing)
        use_case = RegisterBooksBatchUseCase(transaction=transaction, event_bus=event_bus)
        items = [
            RegisterBookBatchItem(
                title="First — would succeed alone", isbn=make_isbn(11), price_cents=999
            ),
            RegisterBookBatchItem(
                title="Second — duplicates an existing book", isbn=make_isbn(10), price_cents=999
            ),
        ]

        with pytest.raises(DuplicateIsbnError):
            await use_case.execute(RegisterBooksBatchCommand(items=items))

        # The whole batch rolled back — including the first item, which
        # would have succeeded if it had been registered on its own. Only
        # the pre-existing book remains.
        assert len(repository.books) == 1
        assert received_events == []

    async def test_rolls_back_the_whole_batch_on_a_duplicate_within_the_batch_itself(
        self,
        repository: InMemoryBookRepository,
        transaction: FakeCatalogTransaction,
        event_bus: EventBus,
        received_events: list[object],
    ) -> None:
        use_case = RegisterBooksBatchUseCase(transaction=transaction, event_bus=event_bus)
        shared_isbn = make_isbn(20)
        items = [
            RegisterBookBatchItem(title="First copy", isbn=shared_isbn, price_cents=999),
            RegisterBookBatchItem(
                title="Second copy, same ISBN", isbn=shared_isbn, price_cents=1499
            ),
        ]

        with pytest.raises(DuplicateIsbnError):
            await use_case.execute(RegisterBooksBatchCommand(items=items))

        # The first item was `add()`-ed to the *shared* session before the
        # second item's `get_by_isbn` check ran, and caught it — exactly
        # the read-your-writes-within-one-transaction property a
        # session-per-method repository can't provide.
        assert len(repository.books) == 0
        assert received_events == []
