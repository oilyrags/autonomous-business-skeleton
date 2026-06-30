.PHONY: sync up up-infra down logs test lint typecheck fmt check build smoke wait-idp

sync:        ## install the uv workspace
	uv sync

build:       ## build the service image
	docker compose build

up:          ## build + bring up the full stack (infra + 5 services)
	docker compose up -d --build --wait

up-infra:    ## bring up only infra (OPA, Redpanda, Postgres, Keycloak) — for in-process tests
	docker compose up -d --wait opa redpanda postgres keycloak

wait-idp:    ## block until the Keycloak realm is serving JWKS
	@echo "waiting for keycloak realm 'ab'..."
	@for i in $$(seq 1 90); do \
		curl -fsS http://localhost:18083/realms/ab/protocol/openid-connect/certs >/dev/null 2>&1 \
		&& echo "idp ready" && exit 0; sleep 2; done; \
		echo "idp not ready after 180s" && exit 1

smoke: wait-idp  ## drive the containerized agent end-to-end and show the audit trail
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
