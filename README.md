# Autonomous AI-First Business Skeleton

The **operating system of an AI-run business**: a reusable, domain-driven architecture skeleton on which many business ideas can be launched, operated, scaled, pivoted, or shut down without rebuilding the foundation. AI-first, open-source-preferred, privacy-preserving (GDPR-first), audit-ready, and deterministic where it must be (money, identity, access, consent, irreversible actions).

This repo is **both the design package and a working reference implementation** of its core loop.
Licensed under [Apache 2.0](LICENSE).

## Quickstart — pick your tier

| Tier | Command | Needs | What you get |
|---|---|---|---|
| **1 · 60-second story** | `uv sync && make demo-lite` | Python + uv only | The whole loop on deterministic stubs: experiments decide → capital reallocates → real-ledger economics → marketing publishes → monitoring checks → the console renders. No Docker, no keys. |
| **2 · Control plane** | `make console-serve` | Python + uv only | The GUI at `http://localhost:8600` — fleet dashboard, business detail, experiments, audit explorer, kill switch ([guide](docs/console.md)). |
| **3 · Governed loop, live** | `make up-infra && make demo` | Docker | The core loop against real infra (Keycloak identity, OPA, Postgres ledger, Redpanda bus) — every control fires. |
| **4 · Secure stack** | `make up && make smoke` | Docker (heavier) | The full SPIFFE/SPIRE mTLS mesh, network-isolated Postgres, containerized services. |

Every demo is also addressable through one CLI: `./abctl --help`
(`./abctl demo` = tier 1; `./abctl loop`, `./abctl social`, `./abctl monitor`, … for single acts).

## The governed loop

Every agent action flows through one ingress where each control fires in order — LLMs reason; deterministic systems execute:

```
agent identity (OIDC)  →  gateway  →  kill-switch (fail-closed)  →  OPA authorize (default-deny)
   →  tool registry (untrusted-input fail-closed · egress data-classification guard)
   →  deterministic tool  ·  ledger (double-entry · cap · maker-checker · payee allow-list · idempotent)
   →  hash-chained audit  →  domain event on the bus  →  data platform (medallion → canonical KPIs)
```

Run it end-to-end and watch every control fire:

```
make up-infra && make demo
```
```
[2] approved payment (double-entry ledger, maker-checker)      -> 200 ok; external:acme = 40000; trial_balance = 0
[3] a prompt-injected payment on an untrusted-input flow       -> 403 sensitive tool blocked under untrusted-input flow
[4] an over-cap payment without a second approver              -> 403 ledger rule: payment 500000 > cap 100000 — needs a checker
[5] the audit log is a hash chain                              -> chain intact
[6] the Finance context published LedgerEntryPosted            -> 1 event on the bus
[7] the data platform serves canonical KPIs                    -> decisions_recorded_total = 1 ...
```

## Implementation

A Python monorepo under [`src/`](src/) (uv workspace; ruff + mypy-strict + pytest). Bounded-context packages:

| Package | Context | What it does |
|---|---|---|
| `ab_identity` | Identity | OIDC agent tokens (Keycloak, RS256/JWKS), revocation |
| `ab_gateway` | Model & agent platform | single ingress; OPA authz; **tool registry** (`decision_registry.write`, `notify.external`, `payments.transfer`); untrusted-input + egress guards |
| `ab_evals` | AI platform | **eval / promotion gate** — a model serves only if it passes capability + safety + grounding + Art.22 bias thresholds |
| `ab_ledger` | Finance | **deterministic double-entry ledger** (integer minor units) — balance invariant, cap, maker-checker + SoD, payee allow-list, idempotency |
| `ab_compliance` | Compliance | **RoPA lawful-basis gate** + **DSAR erasure** with legal hold (Art.17) |
| `ab_ops` | Reliability | error budget, release freeze, **auto-rollback** on Sev1, breach assessment |
| `ab_data` | Data platform | AgentDecisionMade → medallion (DuckDB + dbt) → **canonical KPIs**, freshness SLA, readiness gate |
| `ab_killswitch` / `ab_audit` / `ab_common` / `ab_schemas` | Security / Data | kill switch; tamper-evident hash-chained audit; bus/DB/config; event & request contracts |

Secure-by-default: `make up` runs a full **SPIFFE/SPIRE mTLS mesh** (agent↔gateway, gateway↔OPA, all DB clients, and the Redpanda bus), with Postgres and Redpanda network-isolated. Real models plug in via **Portkey** (`AB_MODEL_PROVIDER=portkey`) and must pass the eval gate to serve.

## Verification — build-proven

The [verification report](architecture/16_verification_report.md) ran 12 audits; **all pass, 0 CONDITIONAL**, each with a runnable proof in CI:

| Gate | Proves |
|---|---|
| `make eval` | AI (Audit 9): eval gate blocks a bad model; grounding + Art.22 bias enforced |
| `make ledger` | Finance (Audit 7): balance invariant, double-payment prevention, maker-checker |
| `make compliance` | Compliance (Audit 4): personal data has a lawful basis + RoPA record |
| `make failsim` | Failure-injection (Audit 12): **7/7 scenarios contained**, 0 breach |
| `make up` + verify scripts | Security (Audit 6): kill-switch SLA, prompt-injection & exfiltration, full mTLS mesh |
| `make check` | lint + mypy-strict + integration tests against the live stack |

## Run it

```
make up-infra     # OPA, Redpanda, Postgres, Keycloak, Vault (host ports)
make demo         # the end-to-end walkthrough above
make check        # lint + types + integration tests
make up           # the full secure-by-default mTLS mesh (containerized services)
make down
```

## The design package

Mode B (Build Specification) — the authoritative design the implementation realizes:

| | Artifact | | Artifact |
|---|---|---|---|
| 00 | [Enterprise overview](architecture/00_enterprise_overview.md) | 09 | [Compliance architecture](architecture/09_compliance_architecture.md) |
| 01 | [Context map](architecture/01_context_map.mermaid) | 10 | [Security architecture](architecture/10_security_architecture.md) |
| 02 | [Ubiquitous glossary](architecture/02_ubiquitous_glossary.md) | 11 | [Model & agent architecture](architecture/11_model_and_agent_architecture.md) |
| 03 | [Domain catalog](architecture/03_domain_catalog.md) | 12 | [Technology stack](architecture/12_tech_stack.md) |
| 04 | [Event catalog](architecture/04_event_catalog.md) + [AsyncAPI](architecture/events.asyncapi.yaml) | 13 | [Decision operating system](architecture/13_decision_operating_system.md) |
| 05 | [Agent registry](architecture/05_agent_registry.json) | 14 | [Instantiation guide](architecture/14_instantiation_guide.md) |
| 06 | [Autonomy authority matrix](architecture/06_autonomy_authority_matrix.md) | 15 | [Implementation roadmap](architecture/15_implementation_roadmap.md) |
| 07 | [Data model](architecture/07_data_model.md) + [inventory](architecture/08_data_inventory_template.json) | 16 | [Verification report](architecture/16_verification_report.md) |

Architecture Decision Records live in [`docs/adr/`](docs/adr/) (0001–0030). **[PROJECT.md](PROJECT.md)** is the living tracker (status, decisions, change log).

## Scope

This is a **skeleton** — the reusable foundation with every core pattern built and proven end-to-end. Launching a real venture on it (per-domain analytics, the CRM/Support/Product contexts, production IdP/secrets, observability) is instantiation work; the patterns those would follow are already demonstrated here.
