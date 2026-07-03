# PRD 0007 — Experimentation & Growth: governed ideation → `growth.experiment.create` → decide

> Triage: `ready-for-agent`. Source: `ideate.md` (2026-07-03), reconciled to the skeleton via
> `/grill-with-docs`. Decisions: ADR-0058 (grilled). Builds on `ab_growth`, the governed
> `ab_gateway` (tool registry + `authz` + OPA, per ADR-0057), `ab_ledger`, `ab_audit`, `ab_data`,
> `ab_console` (operator auth, VULN-001), `ab_ads`, `model_gateway`/`ab_evals`, and the agent
> registry. Tracker: no `gh` → issues under `.scratch/growth/`.

## Problem statement

The Experimentation & Growth domain today is a **deterministic decision engine with no way in**.
`ab_growth.decide()` scores an experiment's evidence into SCALE/PIVOT/KILL/CONTINUE, but there is
no governed way for an agent or an operator to *request* an experiment on a new idea, no persistence
of experiments, no runner feeding live data into `decide`, and no ideation. `ideate.md` proposes a
multi-agent ideation engine that produces grounded, novel, experiment-ready ideas and drives a new
gateway tool `growth.experiment.create`. This PRD reconciles that proposal with the skeleton's
invariants (single governed ingress; deterministic where money/guardrails are decided; `business_id`
tenancy; ports+stubs; infra-free CI) and sequences it as thin vertical slices.

## Solution

A governed, skeleton-native path from **idea → experiment → decision**, built tracer-bullet first:

1. A new **deterministic gateway tool `growth.experiment.create`** — tenant-bound, OPA-authorized,
   affordability-gated, persisted, audited, event-emitting. *This is the load-bearing integration
   point; everything else is a producer or consumer of it.*
2. An **operator console form** ("Propose Experiment for Business X") behind the VULN-001 operator
   auth, calling the tool through the single governed path via a `GrowthPort`.
3. A **runner + decide loop** that feeds `ab_ads` + MVP conversion data into the existing
   *deterministic* `ab_growth.decide()` and emits outcomes.
4. A **skeleton-native multi-agent ideation engine** (`ab_growth/ideate.py`) that produces
   structured, scored, grounded idea candidates and prepares experiment specs — pure orchestration
   over an injected LLM port, deterministic in CI, real GLM-5.2 behind the same seam.

The LLM proposes and annotates; deterministic code decides money and guardrails. Ideation becomes
just another governed producer of `growth.experiment.create` calls — **no change to core
governance**.

## Grilled decisions (ADR-0058)

1. **Tracer bullet = the `growth.experiment.create` gateway tool.** Everything else is a
   producer/consumer of it. (Not the ideate engine, console form, or runner first.)
2. **Deterministic `decide` stays authoritative.** `ab_growth.decide()` remains the sole authority
   for SCALE/PIVOT/KILL/CONTINUE and any capital move. The LLM may *propose* experiments and attach
   *advisory* narrative; it never gates money. (No LLM/Bayesian-LLM decide.)
3. **Reuse the declared agents; add none.** `growth.experiment_design_agent` (L3) owns
   `growth.experiment.create`; grounding = `data.retrieval_grounding_agent` +
   `data.semantic_metrics_agent`; idea-gen/validation = `growth.analysis_agent`; conclusion =
   `growth.analysis_agent` via deterministic `decide`. Ideation is `model_gateway.complete()` calls
   made under these existing identities.
4. **Budget is an affordability *gate*, not a cash movement.** `create` gates through
   `authz.serves_business` + factory readiness + `can_spend(budget)` against current cash; budget is
   recorded as a **cap**. Real money still flows only through the existing ad/LLM rails (no
   double-entry). The runner enforces the cap. A true ledger earmark is a documented follow-up.
5. **New `experiments` table + `ab_growth/store.py` + `ExperimentCreated` event.** Mirrors
   `ab_factory`; pure `decide()` untouched; `business_id`-scoped; idempotent on `experiment_id`.
6. **Ideation lives in `ab_growth/ideate.py`, ports + stub LLM.** Pure orchestration core calls an
   injected `IdeationModel` port (the `model_gateway` seam) and a `GroundingSource` port (`ab_data`
   reads). A `StubIdeationModel` makes ground→generate→validate→design deterministic in CI; real
   GLM-5.2 plugs in via Portkey (the `ab_evals` gate applies).
7. **Console→gateway hop uses a service agent identity + operator in metadata.** The console calls
   under a credential mapped to `growth.experiment_design_agent`; the verified operator id
   (VULN-001) is recorded as `maker`/metadata — dual attribution, one governed path. Delivered via a
   `GrowthPort` (stub + Http adapter), mirroring `KillSwitchPort`/`ApprovalPort`.
8. **LLM scores, deterministic gate.** The Validator emits per-dimension rubric scores (advisory,
   structured output); a **pure** function applies the threshold gate (overall ≥ 3.5 AND novelty ≥ N
   AND grounding ≥ G) → PROCEED/REFINE/KILL. Replayable even though scores are model output; an idea
   without cited grounding sources is capped (anti-hallucination). Mirrors `ab_social` composite
   scoring + the `ab_evals` promotion gate.

## Ubiquitous language (additions — see CONTEXT-MAP)

- **Experiment proposal** — a persisted, governed request to run an experiment: `experiment_id`,
  `business_id`, hypothesis, arms, `budget_minor` (a cap), success metrics, `status`.
- **Experiment status** — `proposed → running → concluded` (`concluded` carries the `decide` action).
- **Arm** — a named variant of the experience (`control`, `treatment[…]`) with an optional
  `implementation_params`. 2–5 arms; the tracer bullet + `decide` use the control/variant pair.
- **Idea candidate** — a scored, grounded, experiment-ready concept (schema below); the ideation
  engine's unit of output.
- **Advisory narrative** — LLM-authored explanation attached to a proposal or outcome; never gates
  money, always clearly separated from the deterministic verdict.
- **Ideation gate** — the pure function that turns rubric scores → PROCEED/REFINE/KILL.

## Slices (vertical, tracer-bullet first)

**E1 — `growth.experiment.create` (tracer bullet).**
- `ab_schemas.models.ExperimentCreate` arg model (`business_id`, `hypothesis`, `arms`,
  `budget_minor`, `success_metrics`, `duration_days`, `target_sample_size`, `metadata`).
- `ab_schemas.events.ExperimentCreated` event (mirror `ExperimentConcluded`: `business_id`,
  `experiment_id`, `hypothesis`, `arm_names`, `budget_minor`, `status="proposed"`).
- `experiments` table in `ab_common/db.py` DDL + `ab_growth/store.py` (`create`, `get`,
  `list_open`, idempotent on `experiment_id`, `business_id`-scoped).
- `tools.create_experiment(principal, args)`: validate → `authz.serves_business` (VULN-002) →
  factory readiness + `can_spend(budget)` (affordability gate) → persist → emit `ExperimentCreated`
  → return `experiment_id`. `ToolDenied` on every business-rule refusal (audited deny, never a 500).
- Register in `tools.REGISTRY` (`side_effect="write"`, `sensitive=True`, `emits_decision=False`);
  OPA rule granting `growth.experiment_design_agent` the action, tenant-bound (extend
  `agent_businesses`); `authz` grant for the agent.
- Tests (infra-free): denial on unauthorized principal / cross-tenant / unaffordable / bad args;
  happy path persists + emits; idempotent replay.

**E2 — Console "Propose Experiment for Business X".** `GrowthPort` (stub + `HttpGrowthPort` → gateway
under the service agent identity); a form behind operator auth + mutating role + origin check
(VULN-001); business selector, hypothesis, arms, budget, success metrics; POST → `GrowthPort.create`
carrying operator id as `maker`; the `/experiments` view reads the real `experiments` table (open +
concluded). Deterministic view-model tests + route tests with the auth headers.

**E3 — Runner + decide loop.** `ab_growth/runner.py`: a pure `collect(experiment, ad_stats,
mvp_stats) → Experiment` that assembles arm impressions/conversions/spend from injected `ab_ads` +
MVP reads, then `decide(exp, blueprint)`; emits `ExperimentConcluded` + a capital signal to
portfolio; enforces the budget cap (stop when spend ≥ cap). Ports for the data reads; stub-driven
CI test proving the full create→run→conclude loop deterministically.

**E4 — Ideation engine (`ab_growth/ideate.py`).** Ports: `IdeationModel` (over `model_gateway`) and
`GroundingSource` (over `ab_data`/`ab_obs` reads). Pure orchestration: ground → generate (3–5
candidates) → validate/score → gate (pure `ideation_gate`) → design experiment spec for
PROCEED ideas. `StubIdeationModel` + `StubGroundingSource` make it deterministic; output is an
`ExperimentCreate` payload ready for E1. Tests assert the gate, the schema, and that low-scored /
un-grounded ideas are filtered.

**E5 — Wire ideation → governed create.** The Experiment Designer step calls `growth.experiment.create`
through the gateway under `growth.experiment_design_agent` (real mode) or returns the payload
(simulation mode). End-to-end: prompt/business context → grounded idea → scored/gated → governed
experiment. A `make ideate` / `./abctl ideate` demo, and an InboxIQ-style worked example.

**E6 — Data platform + docs.** `ExperimentCreated`/`ExperimentConcluded` projections in `ab_data`
(open-experiment count, win rate, budget utilization per `business_id`); console/Grafana surfacing;
CONTEXT.md + CONTEXT-MAP + ADR shipped notes.

**E7 — Growth & Ideation workspace UI (daisyUI + Tailwind).** The full-fidelity operator interface
for this domain, built with the **agreed design system** — daisyUI 5 + the Tailwind 4 browser
runtime, **vendored** (no CDN, no Node toolchain), business/corporate themes — exactly as
ADR-0056 v0.3 established for the console. A dedicated **"Growth" workspace** (new nav entry,
`/growth`), operator-authed (VULN-001), consistent with the existing Fleet/Decisions/Experiments
chrome. It composes the earlier slices into one screen; each panel is a deterministic pure
view-model over an injectable provider, infra-free-tested, and preview-verified in both themes:

- **Ideate panel** — "Launch Ideate for Business X": a business selector + a prompt/context field
  → runs `ab_growth/ideate.py` (E4) via an injected provider → renders **idea candidate cards**
  (title, one-line hook, differentiation, `expected_impact`) with **rubric score badges** (semantic
  green/amber/red via the existing `*_badge` filter pattern), **grounding sources** listed
  (citations required — un-grounded ideas visibly capped), and the **gate verdict** chip
  (PROCEED / REFINE / KILL). A PROCEED idea has a one-click **"Propose"** that pre-fills E2's form.
- **Propose panel** — E2's `growth.experiment.create` form, promoted into the workspace (governed
  `GrowthPort`, operator recorded as `maker`); manual proposal without running Ideate stays possible.
- **Open experiments panel** — `proposed`/`running` rows from the `experiments` table
  (`store.list_open`, tenant-scoped): hypothesis, arms, budget cap, status; a `table table-zebra`.
- **Outcomes panel** — concluded experiments with the statistics visible (the existing
  `/experiments` outcomes table + the E3 `ExperimentConcluded` decision/lift/p-value), decision
  badge, deep-linked to the business.

Design discipline (unchanged from ADR-0056 v0.3): the workspace adds **no new CSS framework and no
build step** — only daisyUI components + the vendored assets already in `static/vendor/`; any custom
rule goes in the thin `console.css` layer; dark/light parity; keyboard-navigable, focus-visible,
semantic HTML + ARIA. Advisory LLM narrative (idea rationale, "why treatment wins in segment Y") is
rendered as clearly-labelled advisory text, visually distinct from the deterministic gate/decision
verdicts (the determinism line is legible in the UI, not just the code).

Depends on E2 (propose form + `GrowthPort`) and E4 (ideation engine) for the Ideate panel; the
Open-experiments and Outcomes panels can land as soon as E1/E3 exist. Tests: pure view-model tests
per panel + route tests behind the operator auth; live preview screenshots in both themes.

## Structured idea schema (maps `ideate.md` §3 → our types)

`IdeaCandidate` (pydantic, in `ab_growth/ideate.py`): `idea_id`, `title`, `one_line_hook`,
`full_description`, `differentiation`, `mvp_notes`, `expected_impact` (primary_metric,
estimated_lift, secondary_metrics, business_case), `risks`, `grounding_sources: list[str]` (must be
non-empty to score above the grounding floor), `scores` (novelty/feasibility/market/grounding/
experiment_clarity 1–5), `overall: float`, and an embedded `experiment: ExperimentCreate`. Tenancy is
**`business_id`**, not `tenant_id` (rename from the doc). The gate reads `scores` + `grounding_sources`.

## Determinism boundaries (the audit line)

| Deterministic (replayable, may gate money) | Advisory (LLM, never gates money) |
|---|---|
| `decide()` SCALE/PIVOT/KILL/CONTINUE; affordability gate; `ideation_gate` threshold; ledger cap enforcement; OPA + `authz` tenant/authority checks | idea generation; rubric *scores*; "why is treatment winning in segment Y" narrative; hypothesis prose |

## Out of scope / follow-ups (logged, not silently dropped)

- **Ledger earmark** of experiment budget (reserve→settle-on-conclude) — deferred; affordability
  gate first (decision 4). Revisit when concurrent-experiment over-commitment is real.
- **Multi-arm (>2) `decide`** — `decide` is control/variant today; N-arm is a later extension.
- **Bayesian/sequential test** — a *deterministic* pluggable test was offered and declined for now
  (decision 2 chose the simpler path); can be added per-Blueprint without touching the LLM boundary.
- **New registry agents / LangGraph/CrewAI** — not needed (decision 3); revisit only if ideation
  outgrows sequential `model_gateway` calls.
- **`tenant_id` naming, `ExperimentCreated` vs the doc's fields** — normalized to `business_id` and
  the repo's envelope.

## Success criteria

An operator (or `growth.experiment_design_agent`) can propose an experiment on a new idea through the
**single governed path** — tenant-bound, affordability-gated, audited, event-emitting — from the
console form or from the ideation engine; a runner drives it to a **deterministic** decision on live
data; and every step is replayable and attributable to both the agent and (when operator-initiated)
the human. All infra-free-testable; ruff + mypy-strict + pytest green.
