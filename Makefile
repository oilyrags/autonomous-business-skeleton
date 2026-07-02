.PHONY: sync up up-infra down logs test lint typecheck fmt check data eval ledger compliance failsim growth factory portfolio econ llm-budget loop revenue ads mvp sales obs playbook memory org sandbox social monitor monitor-submit console console-serve demo build smoke wait-idp seed-vault spire-up spire-verify spire-mtls spire-mtls-verify spire-rotation-drill spire-secure-verify spire-bus-verify

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

growth:      ## experimentation engine demo — scale/pivot/kill decisions per business
	PYTHONPATH=src uv run python -m ab_growth

portfolio:   ## portfolio allocation demo — recycle capital from losers into winners
	PYTHONPATH=src uv run python -m ab_portfolio

econ:        ## unit-economics demo — profit/CAC/margin/LLM-cost per business + budget guard
	PYTHONPATH=src uv run python -m ab_econ

llm-budget:  ## gateway enforces the per-business LLM budget — denies a call before inference
	PYTHONPATH=src uv run python -m ab_gateway.llm_budget_demo

loop:        ## end-to-end: ledger spend → econ verdict → portfolio holds the money-losers
	PYTHONPATH=src uv run python -m ab_portfolio.loop_demo

revenue:     ## revenue rail demo — customer charges booked to the ledger as income (stub rail)
	PYTHONPATH=src uv run python -m ab_revenue

ads:         ## paid-acquisition demo — campaigns spend ledger money, attribute conversions (stub)
	PYTHONPATH=src uv run python -m ab_ads

mvp:         ## MVP generator demo — Blueprint -> landing page -> deployed URL (stub deployer)
	PYTHONPATH=src uv run python -m ab_mvp

sales:       ## sales pipeline demo — qualify -> quote -> close; won deals become ledger revenue
	PYTHONPATH=src uv run python -m ab_sales

obs:         ## observability demo — fleet overview + cost attribution + anomaly detection
	PYTHONPATH=src uv run python -m ab_obs

playbook:    ## living-playbook demo — distil winners into a reusable blueprint, then instantiate
	PYTHONPATH=src uv run python -m ab_playbook

memory:      ## per-business memory demo — scoped recall, no cross-business leakage (stub store)
	PYTHONPATH=src uv run python -m ab_memory

org:         ## hierarchical org demo — authority-based decision routing + escalation to human
	PYTHONPATH=src uv run python -m ab_org

sandbox:     ## tool-sandbox demo — capability allow-list enforcement + audit (stub sandbox)
	PYTHONPATH=src uv run python -m ab_sandbox

social:      ## social content demo — plan -> generate -> QA -> publish (stub gen + publisher)
	PYTHONPATH=src uv run python -m ab_social

monitor:     ## monitoring demo — deterministic checks rendered as Nagios plugin results
	PYTHONPATH=src uv run python -m ab_monitor

monitor-submit: ## submit the check suite to a live Icinga2 (needs docker-compose.monitoring.yml + ICINGA2_API_PASSWORD)
	PYTHONPATH=src uv run python -m ab_monitor.submit

console:     ## console render smoke — the Fleet Dashboard renders through the design system
	PYTHONPATH=src uv run python -m ab_console

console-serve: ## run the console locally (http://localhost:8600)
	PYTHONPATH=src uv run uvicorn ab_console.app:app --port 8600

factory:     ## business factory demo — provision + readiness-gate businesses (per business_id)
	PYTHONPATH=src uv run python -m ab_factory

demo:        ## end-to-end walkthrough of the whole loop (needs `make up-infra`)
	PYTHONPATH=src uv run python scripts/demo.py

data:        ## (batch) consume decisions from the bus, build the warehouse, print KPIs
	PYTHONPATH=src uv run python -m ab_data

data-verify: ## verify the running data service serves canonical KPIs from live events
	./scripts/data-verify.sh

check: lint typecheck test  ## everything CI runs
