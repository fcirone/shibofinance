.PHONY: up down logs migrate test api-shell web-dev web-build web-lint web-types

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

web-dev:
	docker compose run --rm --service-ports web npm run dev

web-build:
	docker compose run --rm web npm run build

web-lint:
	docker compose run --rm web npm run lint

web-types:
	docker compose run --rm web npx openapi-typescript http://api:8000/openapi.json -o src/lib/api-types.ts
