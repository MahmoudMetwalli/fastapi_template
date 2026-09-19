"""Kept thin, per the project plan: status codes, serialization shape, and
error mapping. Business rules are already covered by
`tests/unit/catalog/` and `tests/application/catalog/`.
"""

from httpx import AsyncClient

from tests.factories import make_isbn


class TestRegisterBook:
    async def test_returns_201_with_the_new_book_id(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/books",
            json={"title": "Domain-Driven Design", "isbn": make_isbn(100), "price_cents": 4999},
        )

        assert response.status_code == 201
        assert "id" in response.json()

    async def test_a_duplicate_isbn_returns_409(self, client: AsyncClient) -> None:
        payload = {"title": "Domain-Driven Design", "isbn": make_isbn(101), "price_cents": 4999}
        await client.post("/api/v1/books", json=payload)

        response = await client.post(
            "/api/v1/books",
            json={"title": "A different title", "isbn": make_isbn(101), "price_cents": 1999},
        )

        assert response.status_code == 409

    async def test_a_non_positive_price_is_rejected_before_reaching_the_domain(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/books",
            json={"title": "Domain-Driven Design", "isbn": make_isbn(102), "price_cents": 0},
        )

        assert response.status_code == 422


class TestRegisterBooksBatch:
    async def test_returns_201_with_every_id_in_the_batch(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/books/batch",
            json={
                "items": [
                    {"title": "Domain-Driven Design", "isbn": make_isbn(140), "price_cents": 4999},
                    {"title": "Clean Architecture", "isbn": make_isbn(141), "price_cents": 3499},
                ]
            },
        )

        assert response.status_code == 201
        assert len(response.json()["ids"]) == 2

    async def test_a_duplicate_within_the_batch_rolls_back_the_whole_batch(
        self, client: AsyncClient
    ) -> None:
        shared_isbn = make_isbn(142)
        response = await client.post(
            "/api/v1/books/batch",
            json={
                "items": [
                    {"title": "First copy", "isbn": shared_isbn, "price_cents": 999},
                    {"title": "Second copy, same ISBN", "isbn": shared_isbn, "price_cents": 1499},
                ]
            },
        )

        assert response.status_code == 409

        listed = await client.get("/api/v1/books", params={"title_contains": "copy"})
        assert listed.json()["items"] == []

    async def test_an_empty_batch_is_rejected_before_reaching_the_domain(
        self, client: AsyncClient
    ) -> None:
        response = await client.post("/api/v1/books/batch", json={"items": []})
        assert response.status_code == 422


class TestGetBook:
    async def test_returns_the_registered_book(self, client: AsyncClient) -> None:
        created = await client.post(
            "/api/v1/books",
            json={"title": "Clean Architecture", "isbn": make_isbn(110), "price_cents": 3499},
        )
        book_id = created.json()["id"]

        response = await client.get(f"/api/v1/books/{book_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Clean Architecture"
        assert body["price_cents"] == 3499

    async def test_returns_404_for_an_unknown_id(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/books/00000000-0000-7000-8000-000000000000")
        assert response.status_code == 404


class TestChangeBookPrice:
    async def test_changes_the_price(self, client: AsyncClient) -> None:
        created = await client.post(
            "/api/v1/books",
            json={"title": "Refactoring", "isbn": make_isbn(120), "price_cents": 4999},
        )
        book_id = created.json()["id"]

        response = await client.patch(
            f"/api/v1/books/{book_id}/price", json={"new_price_cents": 2999}
        )
        assert response.status_code == 204

        fetched = await client.get(f"/api/v1/books/{book_id}")
        assert fetched.json()["price_cents"] == 2999


class TestListBooks:
    async def test_lists_registered_books(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/books",
            json={"title": "Domain-Driven Design", "isbn": make_isbn(130), "price_cents": 4999},
        )

        response = await client.get("/api/v1/books")

        assert response.status_code == 200
        titles = [item["title"] for item in response.json()["items"]]
        assert "Domain-Driven Design" in titles
