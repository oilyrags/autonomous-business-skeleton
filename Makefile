.PHONY: sync up down logs test lint typecheck fmt check

sync:        ## install the uv workspace
	uv sync

up:          ## bring up the local stack (OPA, Redpanda, Postgres + service placeholders)
	docker compose up -d --wait

down:        ## tear down the local stack
	docker compose down -v

logs:        ## tail the stack logs
	docker compose logs -f

test:        ## run the test suite
	uv run pytest

lint:        ## lint + format check
	uv run ruff check src
	uv run ruff format --check src

typecheck:   ## strict type check
	uv run mypy

fmt:         ## auto-format
	uv run ruff format src
	uv run ruff check --fix src

check: lint typecheck test  ## everything CI runs
