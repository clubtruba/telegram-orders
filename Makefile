.PHONY: up down test lint migrate

up:
	docker compose up --build

down:
	docker compose down

test:
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check app tests

migrate:
	docker compose run --rm api alembic upgrade head
