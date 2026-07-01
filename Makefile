.PHONY: sync up up-infra down logs test lint typecheck fmt check build smoke wait-idp seed-vault spire-up spire-verify spire-mtls spire-mtls-verify spire-rotation-drill

sync:        ## install the uv workspace
	uv sync

build:       ## build the service image
	docker compose build

seed-vault:  ## write agent client secrets into Vault (KV v2)
	docker compose exec -T vault vault kv put secret/ab/clients \
		executive.cmo_agent=cmo-secret executive.intern_agent=intern-secret

up:          ## build + bring up the full stack (infra + 5 services) + seed Vault
	docker compose up -d --build --wait
	$(MAKE) seed-vault

up-infra:    ## bring up only infra (OPA, Redpanda, Postgres, Keycloak, Vault) + seed — for in-process tests
	docker compose up -d --wait opa redpanda postgres keycloak vault
	$(MAKE) seed-vault

spire-up:    ## build SPIRE, bootstrap the trust domain, start the agent (SPIFFE identity plane)
	./scripts/spire-bootstrap.sh

spire-verify: ## verify SVID issuance + an agent<->gateway mTLS handshake
	./scripts/spire-verify.sh

spire-mtls:  ## bring up the ghostunnel mTLS sidecars (needs `make up` + `make spire-up`)
	docker compose --profile spiffe up -d gateway-proxy agent-proxy

spire-mtls-verify: ## verify a live request routes over SPIFFE mTLS to the gateway
	./scripts/spire-mtls-verify.sh

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
