.PHONY: dev test test-fast lint fmt migrate db-up db-down new-context

dev:
	uv run fastapi dev src/app/main.py

# Scaffold a new bounded context: `make new-context NAME=billing AGGREGATE=Invoice`.
# See README.md's "Adding a new bounded context".
new-context:
	uv run python scripts/new_context.py $(NAME) --aggregate $(AGGREGATE)

# Only unit + application tests: pure domain logic and use cases against
# fakes. No database required — this is the tier meant for a pre-commit
# hook or a tight inner loop.
test-fast:
	uv run pytest tests/unit tests/application

# The full suite, including integration and e2e tiers against Postgres.
test:
	uv run pytest

lint:
	uv run ruff check src tests
	uv run mypy src
	uv run lint-imports

fmt:
	uv run ruff format src tests
	uv run ruff check --fix src tests

migrate:
	uv run alembic upgrade head

db-up:
	docker compose up -d postgres

db-down:
	docker compose down
