from app.contexts.catalog.domain.book import Book
from app.contexts.catalog.domain.events import BookPriceChanged, BookRegistered
from app.contexts.catalog.domain.value_objects import Isbn, Money, Title


def _register(price_cents: int = 4999) -> Book:
    return Book.register(
        title=Title("Domain-Driven Design"),
        isbn=Isbn("9780321125217"),
        price=Money(price_cents),
    )


class TestRegister:
    def test_mints_an_id(self) -> None:
        book = _register()
        assert book.id is not None

    def test_records_a_book_registered_event(self) -> None:
        book = _register()
        events = book.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], BookRegistered)
        assert events[0].book_id == book.id

    def test_pulling_events_clears_them(self) -> None:
        book = _register()
        book.pull_events()
        assert book.pull_events() == []


class TestChangePrice:
    def test_updates_the_price(self) -> None:
        book = _register(price_cents=4999)
        book.change_price(Money(3999))
        assert book.price.amount_cents == 3999

    def test_records_a_price_changed_event(self) -> None:
        book = _register(price_cents=4999)
        book.pull_events()  # discard the registration event
        book.change_price(Money(3999))
        events = book.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], BookPriceChanged)
        assert events[0].old_amount_cents == 4999
        assert events[0].new_amount_cents == 3999

    def test_setting_the_same_price_is_a_no_op(self) -> None:
        book = _register(price_cents=4999)
        book.pull_events()
        book.change_price(Money(4999))
        assert book.pull_events() == []


class TestIdentityEquality:
    def test_two_books_with_the_same_id_are_equal_even_if_other_fields_differ(self) -> None:
        book = _register()
        same_id_different_price = Book(id=book.id, title=book.title, isbn=book.isbn, price=Money(1))
        assert book == same_id_different_price

    def test_two_freshly_registered_books_are_not_equal(self) -> None:
        assert _register() != _register()
