# PRD 0003 — Close the recommendation gaps (P0–P5)

> Triage: `ready-for-agent`. Source: `recommendations.md` (repo review, 2026-07-01). Builds on
> slices 40–49 (portfolio/econ/cost-control core). Tracker: no `gh` → issues under `.scratch/`.

## Problem Statement

The skeleton has a strong deterministic core (governance, ledger, growth, factory, portfolio,
economics), but a July-2026 review found it **infrastructure-heavy**: the capabilities that actually
*generate revenue* and let it run *many* businesses at scale are missing or thin. The owner wants
every gap in `recommendations.md` (P0–P5) closed so the skeleton is end-to-end complete: a business
can be instantiated, put a product in front of customers, acquire them, take money, and have capital
follow real profit — all attributable per business and safe by default.

## Solution

Close each gap as a thin **deep module** at the **highest seam** available, following the repo's
established pattern: a **pure decision core** plus, where an external service is involved, an injected
**port** (a `Protocol`) with a **stub adapter** by default and a real adapter behind the same
interface (exactly like `ChatClient` → `StubModel`/`PortkeyModel`, and `InMemoryLedger` → Postgres
`store`). No live third-party credentials are used; every external seam ships a deterministic stub so
the whole loop runs in CI, and a real provider drops in later without touching callers. New distinct
domains become their own `src/ab_*` bounded-context packages; money always flows through the existing
double-entry ledger; every new event and record carries `business_id`.

## User Stories

1. As a business operator, I want revenue received from customers booked into the ledger per
   business, so that unit economics use real income instead of an injected number.
2. As a business operator, I want a revenue-rail port with a stub adapter, so that Stripe/Lemon
   Squeezy can be dropped in later without changing the ledger or econ.
3. As a portfolio manager, I want the econ loop to consume real ledger revenue, so that
   profitability verdicts and capital allocation reflect actual money in and out.
4. As a growth agent, I want ad spend placed through an ad-platform port (stub) and booked to the
   business's ledger account, so that acquisition cost is real and attributable.
5. As a growth agent, I want closed-loop attribution from ad spend to conversions, so that CAC is
   computed from real spend and real customers.
6. As a business operator, I want an MVP/landing-page generated from a Blueprint and "deployed" via a
   deployer port (stub returning a URL), so that an experiment has a real page to point traffic at.
7. As a platform owner, I want the deployer port to be swappable (Vercel/Netlify/container), so that
   real hosting drops in behind the stub.
8. As a sales agent, I want a deterministic pipeline (lead → qualify → quote → close/won →
   renewal/expansion) emitting revenue events, so that closing produces ledger revenue.
9. As a portfolio manager, I want winning-business strategies extracted into versioned, reusable
   Blueprint templates (Living Playbooks), so that what works is captured and reused.
10. As a portfolio manager, I want cross-business "what works" patterns detected over experiment
    outcomes in aggregate, so that learning transfers without leaking per-business detail.
11. As an agent runtime, I want a per-business memory store namespaced by `business_id`, so that an
    agent recalls prior context with no cross-business leakage.
12. As a platform owner, I want the memory store behind a port, so that a vector backend can replace
    the in-memory/Postgres adapter later.
13. As an executive agent, I want a hierarchical org model (charters, teams, escalation) tied to the
    L0–L5 authority matrix, so that decisions route to the right authority and escalate correctly.
14. As a security owner, I want tool execution to run through a sandbox port (stub enforcing a
    capability/resource policy, every call audited), so that E2B/Modal-style isolation drops in later.
15. As a finance analyst, I want LTV, payback period, contribution margin, and a per-business P&L in
    `ab_econ`, so that the full unit-economics picture is available.
16. As an operator, I want cost attribution, spend/conversion anomaly detection, and a per-business +
    fleet overview, so that I can see why money moved and catch anomalies.
17. As an auditor, I want `business_id` on `AgentDecisionMade` and the decisions store, so that every
    material decision is attributable to a business, mirroring the money path.
18. As a reliability owner, I want property-based tests of the ledger approval rules and policy
    enforcement, so that money/authority invariants hold for arbitrary inputs.
19. As a reliability owner, I want failure-injection scenarios for revenue and multi-business faults,
    so that losing-business sunset, over-budget denial, and cross-business isolation are proven under
    fault.
20. As a developer, I want every external seam to run on a stub in CI with no credentials, so that the
    whole loop is verifiable offline and a real provider is a drop-in.

## Implementation Decisions

- **Seam pattern (confirmed):** new `src/ab_*` bounded-context packages; external services behind an
  injected `Protocol` port with a **stub adapter** default + real adapter behind the same interface.
  Pure cores are plain functions/dataclasses/Pydantic, tested directly (prior art: `ab_growth`,
  `ab_econ`, `ab_portfolio`). Money always books through the double-entry ledger; ratios in bps,
  money in integer minor units.
- **Delivery order (confirmed): revenue-facing first**, then pure P3/P4, then P2 runtime.
- **New contexts:** `ab_revenue` (revenue rail port + stub + ledger booking + `RevenueReceived`
  event), `ab_ads` (ad-platform port + stub + ledger ad-spend booking + attribution), `ab_mvp`
  (Blueprint → page artifact + deployer port + stub), `ab_sales` (pure pipeline core + events),
  `ab_playbook` (pattern extraction → versioned Blueprint template), `ab_memory` (per-business memory
  port + in-memory/Postgres adapter), `ab_org` (charters/teams/escalation pure core), `ab_sandbox`
  (tool sandbox port + stub), `ab_obs` (cost attribution + anomaly detection + fleet overview query
  layer over ledger/audit).
- **Existing contexts modified:** `ab_econ` (LTV/payback/contribution-margin/P&L); `ab_schemas`
  (+`RevenueReceived`, `AdSpendPlaced`, `SaleClosed`, `business_id` on `AgentDecisionMade` — the
  AsyncAPI contract test drives each event addition); `ab_common/db.py` (`decisions.business_id`
  column + any new tables); `ab_ledger` (booking helpers reused, not forked); `ab_failsim` (revenue
  scenarios); `ab_gateway` (decision-tool `business_id` propagation).
- **Revenue closes the last synthetic input:** `ab_revenue` books `RevenueReceived` to
  `{business_id}:cash` (credit) / `{business_id}:revenue` (or an income account); `ab_econ` gains a
  `revenue`-side ledger query so the closed loop (`ledger → econ → portfolio`) runs on fully real
  money — extending `ab_ledger.business_spend` into a `business_pnl`/revenue read.
- **Contract & attribution discipline:** every new domain event is added to
  `events.asyncapi.yaml` and passes the ADR-0037 contract test (which fails until model and spec
  match); every new event and persisted row carries `business_id`.
- **Authority alignment:** `ab_org` escalation maps to the existing L0–L5 autonomy matrix; money and
  high-risk actions stay human-in-the-loop (no new L5-for-money path). Sandbox denials and org
  escalations are deterministic.

## Testing Decisions

- **What makes a good test here:** exercise the public interface (the port, the pure function, the
  event/ledger effect), not internals; expected values come from an independent source (worked
  example, the spec), never recomputed the way the code computes them. Stub adapters make external
  seams fully testable in CI with no credentials.
- **Modules tested:** each new context's pure core (unit, infra-free, in the normal CI suite);
  ledger/gateway wiring via integration tests that skip fast without infra (prior art:
  `test_business_spend_store.py`, `test_payment_business_id.py`, `test_llm_budget_wiring.py`); the
  revenue/ad/MVP/sandbox ports via their stub adapters; property-based tests via Hypothesis (prior
  art: `test_ledger_properties.py`, `test_portfolio_properties.py`); each event via the AsyncAPI
  contract test (prior art: `test_asyncapi_contract.py`); an infra-free `make <ctx>` demo per context
  (prior art: `make econ`, `make loop`), wired into CI.
- **Prior art for stub-backed ports:** `ab_gateway.providers` (`ChatClient` Protocol +
  `StubModel`/`PortkeyModel`), `ab_ledger` (`InMemoryLedger` vs Postgres `store`).

## Out of Scope

- Live third-party API calls (real Stripe/Lemon Squeezy charges, real ad buys, real hosting deploys,
  real E2B/Modal sandboxes) — only the ports + stub adapters are built; real adapters are a follow-up
  requiring credentials + platform choice.
- A real vector/embeddings backend for memory (the port + a simple adapter ship; embeddings later).
- A UI/dashboard front-end for observability (the query/rollup layer ships; rendering is later).
- Full LLM agent-reasoning behaviour (the org model routes authority; it does not replace the model).

## Further Notes

Each slice is a tracer bullet: pure core → port/stub (if external) → ledger/event wiring →
`business_id` attribution → AsyncAPI contract (if it emits an event) → `make` demo → tests → ADR.
Sliced in `.scratch/` and implemented via `/tdd`, one behaviour at a time. Revenue-rail first so the
`ledger → econ → portfolio` loop stops being synthetic on the revenue side.
