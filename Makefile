.PHONY: sync up up-infra down logs test lint typecheck fmt check data eval ledger compliance failsim build smoke wait-idp seed-vault spire-up spire-verify spire-mtls spire-mtls-verify spire-rotation-drill spire-secure-verify spire-bus-verify

# Secure-by-default: the stack runs the full SPIFFE mTLS mesh; Postgres is network-isolated
# and reachable only via its mTLS proxy. The in-process test suite uses `up-infra` (plaintext
# infra on the host-published ports) — the containerized app path is always mTLS.
COMPOSE_SECURE := docker compose -f docker-compose.yml -f docker-compose.spiffe.yml --profile spiffe
PROXIES := gateway-proxy agent-proxy opa-proxy gateway-opa-proxy postgres-proxy \
	gateway-pg-proxy audit-pg-proxy killswitch-pg-proxy identity-pg-proxy \
	redpanda-proxy kafka-mtls
APPSVCS := identity gateway killswitch audit agent data

sync:        ## install the uv workspace
	uv sync

build:       ## build the service image
	docker compose build

seed-vault:  ## write agent client secrets into Vault (KV v2)
	docker compose exec -T vault vault kv put secret/ab/clients \
		executive.cmo_agent=cmo-secret executive.intern_agent=intern-secret

up:          ## bring up the full secure-by-default stack (infra -> SPIRE -> mTLS proxies -> services)
	$(COMPOSE_SECURE) up -d --build --wait opa redpanda postgres keycloak vault
	AB_DC="$(COMPOSE_SECURE)" ./scripts/spire-bootstrap.sh
	$(COMPOSE_SECURE) up -d --no-recreate $(PROXIES)
	$(COMPOSE_SECURE) up -d --no-recreate --build --wait $(APPSVCS)
	$(MAKE) seed-vault

up-infra:    ## bring up only infra (OPA, Redpanda, Postgres, Keycloak, Vault) + seed — for in-process tests
	docker compose up -d --wait opa redpanda postgres keycloak vault
	$(MAKE) seed-vault

spire-up:    ## build SPIRE, bootstrap the trust domain, start the agent (SPIFFE identity plane)
	./scripts/spire-bootstrap.sh

spire-verify: ## verify SVID issuance + an agent<->gateway mTLS handshake
	./scripts/spire-verify.sh

spire-mtls:  ## (re)bring up all ghostunnel mTLS sidecars
	$(COMPOSE_SECURE) up -d $(PROXIES)

spire-mtls-verify: ## verify a live request routes over SPIFFE mTLS to the gateway
	./scripts/spire-mtls-verify.sh

spire-secure-verify: ## verify all hops + DB clients run over mTLS (and Postgres is isolated)
	./scripts/spire-secure-verify.sh

spire-bus-verify: ## verify gateway/audit/data <-> Redpanda run over mTLS (produce + consume)
	./scripts/spire-bus-verify.sh

spire-rotation-drill: ## short-TTL SVIDs; prove rotation + zero-downtime mTLS (needs `make up`)
	docker compose --profile spiffe rm -sf spire-server spire-agent gateway-proxy agent-proxy >/dev/null 2>&1 || true
	SVID_TTL=60 ./scripts/spire-bootstrap.sh
	docker compose --profile spiffe up -d gateway-proxy agent-proxy
	./scripts/spire-rotation-drill.sh

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

down:        ## tear down the local stack (incl. mTLS mesh)
	$(COMPOSE_SECURE) down -v

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

eval:        ## run the model promotion gate (blocks a model that fails its eval set)
	PYTHONPATH=src uv run python -m ab_evals

ledger:      ## run the ledger invariants self-check (balance, double-payment, maker-checker)
	PYTHONPATH=src uv run python -m ab_ledger

compliance:  ## RoPA/lawful-basis gate: fail if personal data lacks an 08 record + basis
	PYTHONPATH=src uv run python -m ab_compliance

failsim:     ## run the failure-injection scenario suite (Audit 12); breach -> non-zero
	PYTHONPATH=src uv run python -m ab_failsim

data:        ## (batch) consume decisions from the bus, build the warehouse, print KPIs
	PYTHONPATH=src uv run python -m ab_data

data-verify: ## verify the running data service serves canonical KPIs from live events
	./scripts/data-verify.sh

check: lint typecheck test  ## everything CI runs
