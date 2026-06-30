.PHONY: sync up up-infra down logs test lint typecheck fmt check build smoke

sync:        ## install the uv workspace
	uv sync

build:       ## build the service image
	docker compose build

up:          ## build + bring up the full stack (infra + 5 services)
	docker compose up -d --build --wait

up-infra:    ## bring up only infra (OPA, Redpanda, Postgres) — for in-process tests
	docker compose up -d --wait opa redpanda postgres

smoke:       ## drive the containerized agent end-to-end and show the audit trail
	@curl -fsS -X POST http://localhost:18090/act | python3 -m json.tool
	@echo "--- audit (allow records) ---"
	@curl -fsS "http://localhost:18081/audit?action=decision_registry.write" | python3 -m json.tool

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
