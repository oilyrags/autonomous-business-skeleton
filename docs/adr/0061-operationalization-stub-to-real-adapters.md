---
status: accepted
---

# Operationalization — config-selected real adapters (stub → real), Phase 0+1

How the skeleton goes from stub/sample defaults to a **live** deployment without abandoning the
ports+stubs invariant. Grilled via `/grill-with-docs` against the real selection/eval/identity code
(`ab_gateway/providers.py` `served()`, `ab_gateway/model_gateway.py` eval gate, `ab_evals`,
`ab_console/app.py` `_SAMPLE_` providers + `growth_port.py`/`killswitch_port.py`,
`ab_monitor/icinga2.py`, `config/keycloak/ab-realm.json`, `ab_common/config.py`). Scope: **Phase 0**
(keystone: promote a real model) + **Phase 1** (flip the seams whose real adapter already exists).
Phase 2 (revenue/ads/social real adapters) and Phase 3 (sandbox/deployers/approvals) are deferred to
their own PRDs. Plan: PRD 0009.

## Framing

"Replace the stubs" does **not** mean delete them. Stubs are the deterministic, infra-free **CI
default** (the ports+stubs pattern). Operationalizing = **add/enable the real adapter behind each
existing Protocol and select it by config in a live deployment**, keeping the stub as the fallback
for CI and for advisory seams. The determinism boundary is preserved: LLMs stay advisory + eval-gated;
money / identity / egress / deploy stay deterministic + human-gated.

## Decisions (grilled)

1. **Selection = a per-port env factory.** Generalize the one precedent (`providers.served()` reading
   `AB_MODEL_PROVIDER`, default `"stub"`): each context exposes a `served()`-style factory that reads
   `AB_<PORT>_PROVIDER` and returns the stub or the real adapter. Decentralized (each context owns its
   seam); config flows through the existing `ab_common.config` `_secret()` + `AB_ENV` machinery. No new
   global concept. (Rejected: a central composition-root/container; a per-env profile registry — both
   add a cross-cutting global that fights the context-owns-its-port style.)
2. **Prod defaults fail-closed for critical ports.** A designated set of operational-critical seams —
   money (`ab_revenue` gateway), egress/identity (`ab_ads` platform, `ab_social` publisher,
   `ab_sandbox`, the deployers) — MUST resolve to a real adapter when `AB_ENV=prod` or the app refuses
   to start (the VULN-005 fail-closed posture). Advisory/read seams (ideation/product/social LLM,
   grounding, KPI/econ reads, monitor exporter) may still fall back to stub/abstain. (Rejected: stub
   everywhere unless opted-in — a silent money/egress footgun; fail-closed for ALL ports — blocks the
   phased rollout.)
3. **Model promotion is persisted + explicit.** `PromotionRegistry` is in-memory today, so a real
   model can only promote by evaluating at every boot. Instead: add a **promotions table**; an explicit
   ops/CI `eval-promote` run evaluates the live model **once** against the profile's eval suite and, if
   it passes the gate, records a `ModelPromoted` decision (audited, replayable). The gateway reads the
   persisted registry at boot; a model serves only with a valid recorded promotion. Requires an **eval
   suite per LLM task-profile** (`ideation`, `product_spec`, social) — without it `complete()` abstains
   forever. (Rejected: `AB_EVAL_ON_BOOT=1` re-evaluates every boot — paid/network evals per start,
   startup latency, transient failure degrades the whole fleet to abstain; config-flag promotion —
   bypasses the eval gate, a governance violation.)
4. **Console reads in-process; writes over governed HTTP.** Read providers (fleet→`ab_obs`,
   econ→`ab_econ`, checks→`ab_monitor`, snapshots→`ab_factory`/`ab_portfolio`, audit/experiments/
   products→their stores) import each owning context's **read-only** functions directly — the console
   already builds its view-models this way. State-changing actions (kill switch, propose, approve/DPIA)
   go over **authenticated HTTP** to the governed services. (Rejected: all-over-HTTP — build+auth read
   endpoints on every context service for read-only data; a CQRS read-model store — a large new
   component, disproportionate to current scale.)
5. **One Keycloak client per fronted service-agent.** The console calls the gateway *as* the real
   agent (`growth.experiment_design_agent`, later product) — OPA authorizes agents, not operators. Add
   a Keycloak client per fronted agent (client-credentials, secret in Vault, exactly like the existing
   `cmo`/`intern` clients); the console's `token_provider` picks the client per target tool; the
   operator is recorded as `maker` (dual attribution). (Rejected: one broad "console service account" —
   union of all agents' permissions + wrong attribution; forwarding the operator as principal — OPA
   authorizes agents, and it collapses the agent-acts/operator-approves model.)

## Determinism boundary (unchanged, restated)

| Deterministic / human-gated (must be real in prod) | Advisory / eval-gated (may abstain to stub) |
|---|---|
| revenue charge → income; ledger; ad spend; social publish (egress); sandbox execution; product/mvp deploy; kill switch; every governed tool authz | ideation ideas; product blueprint spec; social content draft; grounding context; model completions (all eval-gated, abstain when no model promoted) |

## Consequences

- A single, uniform way to light up any seam: set `AB_<PORT>_PROVIDER=<real>` + its secret; prod
  refuses to start if a critical seam is left on a stub.
- Model promotion becomes an auditable, one-time, eval-gated decision (a `ModelPromoted` record), not a
  per-boot side effect — and it exposes a real gap: **eval suites must exist per LLM task-profile**.
- The console's live control plane is reads-in-process / writes-over-governed-HTTP, needing a Keycloak
  client per fronted agent.
- Reuses VULN-005 (fail-closed secrets), VULN-001/004 (operator attestation), ADR-0057 (governed
  ingress), the M5 monitoring rail, and the existing eval gate — no new frameworks.

## Deferred (own PRDs)

Phase 2 real adapters — `ab_revenue` (Stripe), `ab_ads` (Google/Meta), `ab_social`
(content/publisher/metrics), `ab_growth` grounding (`ab_data`). Phase 3 — `ab_sandbox` (isolated
execution), `ab_mvp`/`ab_product` deployers (compose `ventures` → k8s/cloud) + scaffold writer,
console approval/product ports (gateway-backed). Each is a per-seam tracer-bullet slice: real adapter
behind the existing port → config flip → integration test → stub stays green in CI.
