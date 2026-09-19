"""Kept thin, per the project convention: status codes and cross-context
wiring. Business rules are covered by `tests/unit/ordering/` and
`tests/application/ordering/`; the Anti-Corruption Layer's own translation
is covered by `tests/integration/ordering/test_catalog_acl.py`. This tier
is the only place that proves the whole thing — `catalog`'s HTTP API,
`ordering`'s HTTP API, and the container-wired ACL between them — actually
works together, over real HTTP, against a real database.
"""

from httpx import AsyncClient

from tests.factories import make_isbn


async def _register_book(client: AsyncClient, *, title: str, isbn: str, price_cents: int) -> str:
    response = await client.post(
        "/api/v1/books", json={"title": title, "isbn": isbn, "price_cents": price_cents}
    )
    book_id: str = response.json()["id"]
    return book_id


class TestPlaceOrder:
    async def test_places_an_order_for_a_book_registered_through_catalog(
        self, client: AsyncClient
    ) -> None:
        book_id = await _register_book(
            client, title="Domain-Driven Design", isbn=make_isbn(200), price_cents=4999
        )

        response = await client.post(
            "/api/v1/orders", json={"items": [{"book_id": book_id, "quantity": 2}]}
        )

        assert response.status_code == 201
        order_id = response.json()["id"]

        fetched = await client.get(f"/api/v1/orders/{order_id}")
        assert fetched.status_code == 200
        body = fetched.json()
        assert body["total_cents"] == 9998
        assert body["lines"][0]["title"] == "Domain-Driven Design"

    async def test_a_later_price_change_in_catalog_does_not_affect_an_existing_order(
        self, client: AsyncClient
    ) -> None:
        book_id = await _register_book(
            client, title="Clean Architecture", isbn=make_isbn(201), price_cents=3499
        )
        placed = await client.post(
            "/api/v1/orders", json={"items": [{"book_id": book_id, "quantity": 1}]}
        )
        order_id = placed.json()["id"]

        await client.patch(f"/api/v1/books/{book_id}/price", json={"new_price_cents": 1})

        fetched = await client.get(f"/api/v1/orders/{order_id}")
        assert fetched.json()["total_cents"] == 3499

    async def test_referencing_a_book_that_does_not_exist_is_rejected(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/orders",
            json={"items": [{"book_id": "00000000-0000-7000-8000-000000000000", "quantity": 1}]},
        )
        assert response.status_code == 422

    async def test_an_empty_order_is_rejected_before_reaching_the_domain(
        self, client: AsyncClient
    ) -> None:
        response = await client.post("/api/v1/orders", json={"items": []})
        assert response.status_code == 422


class TestGetOrder:
    async def test_returns_404_for_an_unknown_id(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/orders/00000000-0000-7000-8000-000000000000")
        assert response.status_code == 404
