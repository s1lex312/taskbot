.PHONY: up down migrate logs lint test

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

lint:
	python -m ruff check .
	python -m black --check .
	python -m isort --check-only .

test:
	python -m pytest
