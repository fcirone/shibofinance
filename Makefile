.PHONY: up down logs migrate test api-shell

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

test:
	docker compose exec api pytest tests/ -v

api-shell:
	docker compose exec api bash
