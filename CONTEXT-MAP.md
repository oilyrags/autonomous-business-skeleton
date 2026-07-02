# Context Map

The reusable operating system of an AI-run business, now realized as **27 bounded contexts** under
`src/`. This map is the entry point: it lists the contexts, the shared language that spans them, and
the key integration flows. Each context owns a tight local glossary in its own `CONTEXT.md`.

**How the engineering skills consume this:** read this map first, then the `CONTEXT.md` of the
context you're working in, then any ADRs in `docs/adr/` that touch it. The authoritative long-form
glossary is `architecture/02_ubiquitous_glossary.md`; per-context `CONTEXT.md` files are its
tightened, opinionated form for day-to-day work.

## Shared language (spans every context)

**Bounded Context**:
An explicit boundary inside which one domain model and its language are consistent; owns its data, integrates only via API, event, or ACL. Each `src/ab_*` package is one.
_Avoid_: module, service, microservice (when you mean the domain boundary)

**business_id**:
The multi-tenancy key that scopes every business's config, events, ledger accounts, budgets, and decisions. One skeleton runs many businesses side by side.
_Avoid_: tenant_id, org_id, account_id

**Minor Units**:
Money as integer minor units (e.g. cents) — never a float — so arithmetic is exact and reproducible. Ratios are integer basis points (bps).
_Avoid_: dollars, decimal, amount (when you mean the integer representation)

**Port / Adapter / Stub**:
A `Port` is an injected `Protocol` at a seam; the `Stub` adapter is the deterministic default (runs in CI, no infra); a real adapter (Postgres, Portkey, Postiz…) implements the same port behind it. The model-provider pattern.
_Avoid_: interface, mock, driver (when you mean this seam)

**Determinism Boundary**:
The rule (architecture/06) that LLMs reason and draft, but deterministic code makes every money / identity / access / compliance decision. LLM output is never a decision.
_Avoid_: guardrail (a Guardrail is the enforced control), safety layer

**Domain Event / Envelope**:
An immutable fact published on the bus, carrying the common `Envelope` (event name, id, producer, classification, subject) defined in `ab_schemas`. Consumers are idempotent by event id.
_Avoid_: message, notification, record

**Walking Skeleton**:
The thinnest end-to-end vertical slice that exercises every foundational concern at once — identity, authorization, audit, events, kill switch — and becomes the spine the rest of the system grows from.
_Avoid_: MVP, prototype, spike (those imply throwaway or scope, not a load-bearing thin slice)

## Contexts

### Platform & governance
- [ab_identity](./src/ab_identity/CONTEXT.md) — SPIFFE/OIDC agent identity and short-lived tokens
- [ab_gateway](./src/ab_gateway/CONTEXT.md) — the single governed ingress: tool registry, policy, model gateway, spend/LLM-budget gates
- [ab_killswitch](./src/ab_killswitch/CONTEXT.md) — revokes credentials and halts tool execution within an SLA
- [ab_audit](./src/ab_audit/CONTEXT.md) — the append-only, hash-chained audit log
- [ab_org](./src/ab_org/CONTEXT.md) — charters, authority levels, and escalation up the reporting chain
- [ab_agent](./src/ab_agent/CONTEXT.md) — the accountable, identity-bearing AI actor runtime
- [ab_sandbox](./src/ab_sandbox/CONTEXT.md) — capability-scoped tool execution sandbox
- [ab_memory](./src/ab_memory/CONTEXT.md) — per-business agent memory, namespaced with no cross-business leakage

### Finance
- [ab_ledger](./src/ab_ledger/CONTEXT.md) — the double-entry ledger: money, invariants, maker-checker
- [ab_econ](./src/ab_econ/CONTEXT.md) — per-business unit economics (CAC, margin, LTV, payback, P&L)
- [ab_revenue](./src/ab_revenue/CONTEXT.md) — the revenue rail: customer charges booked as income

### Growth & portfolio
- [ab_growth](./src/ab_growth/CONTEXT.md) — the experimentation engine (A/B → scale/pivot/kill) + Blueprint
- [ab_factory](./src/ab_factory/CONTEXT.md) — instantiates a business behind a readiness gate, funded with capital
- [ab_portfolio](./src/ab_portfolio/CONTEXT.md) — capital allocation across businesses (recycle losers into winners)
- [ab_playbook](./src/ab_playbook/CONTEXT.md) — Living Playbooks: distil winners into reusable blueprints

### Revenue-facing
- [ab_ads](./src/ab_ads/CONTEXT.md) — paid acquisition: ad-platform port + closed-loop attribution
- [ab_mvp](./src/ab_mvp/CONTEXT.md) — MVP/landing-page generation + deployer port
- [ab_sales](./src/ab_sales/CONTEXT.md) — the sales pipeline (lead → qualify → quote → close)
- [ab_social](./src/ab_social/CONTEXT.md) — multichannel content generation & distribution (marketing)

### Data, AI & compliance
- [ab_data](./src/ab_data/CONTEXT.md) — the warehouse, freshness gate, and canonical metric registry
- [ab_evals](./src/ab_evals/CONTEXT.md) — model eval + promotion gate, grounding and bias gates
- [ab_compliance](./src/ab_compliance/CONTEXT.md) — RoPA, lawful basis, consent, DSAR erasure
- [ab_obs](./src/ab_obs/CONTEXT.md) — observability: fleet overview, cost attribution, anomaly detection

### Reliability & shared
- [ab_ops](./src/ab_ops/CONTEXT.md) — reliability: incidents, error budgets, rollback
- [ab_monitor](./src/ab_monitor/CONTEXT.md) — Nagios monitoring: existing signals → plugin check results
- [ab_console](./src/ab_console/CONTEXT.md) — the human control plane: view-models + HIG design system over the fleet
- [ab_failsim](./src/ab_failsim/CONTEXT.md) — the failure-injection scenario suite
- [ab_schemas](./src/ab_schemas/CONTEXT.md) — shared kernel: domain-event models + tool-arg schemas
- [ab_common](./src/ab_common/CONTEXT.md) — shared infrastructure (Postgres, bus, config, secrets)

### Examples (not bounded contexts)
- [ab_examples](./src/ab_examples/CONTEXT.md) — worked examples composing the contexts end to end (`inboxiq`)

## Relationships

- **ab_gateway governs all tool use** — every agent action routes through it (policy, determinism
  boundary, egress, spend and LLM-budget gates); `ab_identity` issues the caller's identity;
  `ab_killswitch` can halt it; `ab_audit` records it; `ab_org` decides who may authorise / escalate.
- **Money flows through ab_ledger** — `ab_revenue` (charges → income), `ab_ads` (ad spend), the
  gateway (LLM metering), and `ab_factory` (capital) all book to it, attributed by `business_id`.
- **The economic loop**: `ab_revenue`/`ab_ads`/gateway spend → `ab_ledger` → `ab_econ`
  (`business_spend`/`business_revenue` → verdict) → `ab_portfolio` (`unprofitable_business_ids`
  gates allocation). `ab_obs` reads the same ledger for the fleet overview.
- **The growth loop**: `ab_growth` concludes experiments (`ExperimentConcluded`) → `ab_portfolio`
  rolls them into `BusinessPerformance`; `ab_playbook` distils winning `Blueprint`s.
- **The marketing loop**: `ab_social` plans/generates/QA-gates/publishes content
  (`ContentPublished` → `PostMetricsCollected`), reuses `ab_growth` to optimise and `ab_playbook`
  to distil, gates publishing via `ab_org`, and boosts via `ab_ads`.
- **Instantiation**: `ab_factory` provisions a business (funding it via `ab_ledger`), passing a
  readiness gate that reads `ab_compliance` (RoPA) and `ab_killswitch`; emits `BusinessActivated`.
- **AI serving**: `ab_gateway` serves a task profile only via a model `ab_evals` has promoted;
  `ab_data` publishes the canonical metrics decisions are measured against.
