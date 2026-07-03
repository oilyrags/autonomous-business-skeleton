---
status: accepted
---

# Growth ideation + `growth.experiment.create` (governed experimentation)

Reconciles `ideate.md` (an "Agent Ideate"-style multi-agent ideation engine driving a new gateway
tool) with the skeleton's invariants. Designed via `/grill-with-docs`; the stack/fit decisions were
grilled against the actual code (`ab_growth`, `ab_gateway` registry + `authz`/OPA per ADR-0057,
`ab_ledger`, `ab_console` auth per VULN-001, `ab_data`, the agent registry, `model_gateway`). Plan:
PRD 0007.

## Decisions (grilled)

1. **Tracer bullet = the governed `growth.experiment.create` gateway tool** — the doc's "single most
   important integration point". The console form, runner, and ideation engine are producers/
   consumers of it, built in later slices.
2. **Deterministic `decide` stays authoritative.** `ab_growth.decide()` alone decides
   SCALE/PIVOT/KILL/CONTINUE and any capital move (guardrails + statistical test). The LLM proposes
   experiments and attaches *advisory* narrative; it never gates money — upholding "LLMs reason;
   deterministic systems execute" and keeping the audit replayable. (Rejected: LLM/Bayesian-LLM
   decide.)
3. **Reuse the declared agents; add none.** `growth.experiment_design_agent` (L3) owns the tool;
   grounding via `data.retrieval_grounding_agent` + `data.semantic_metrics_agent`; validation via
   `growth.analysis_agent`; conclusion via `growth.analysis_agent` + deterministic `decide`.
   Ideation is `model_gateway.complete()` calls under these existing identities. (Rejected: a new
   `ab_ideate` agent team.)
4. **Budget is an affordability gate, not a cash movement.** `create` gates on
   `authz.serves_business` + factory readiness + `can_spend(budget)` against current cash and records
   the budget as a **cap**; real money flows only through the existing ad/LLM ledger rails (no
   double-entry). The runner enforces the cap. A ledger earmark (reserve→settle) is a follow-up.
5. **New `experiments` table + `ab_growth/store.py` + `ExperimentCreated` event.** The growth context
   gains a thin store (mirroring `ab_factory`); pure `decide()` is untouched; `business_id`-scoped,
   idempotent on `experiment_id`.
6. **Ideation lives in `ab_growth/ideate.py`, skeleton-native.** A pure orchestration core over an
   injected `IdeationModel` port (the `model_gateway` seam) and a `GroundingSource` port (`ab_data`
   reads); a `StubIdeationModel` makes ground→generate→validate→design deterministic in CI; real
   GLM-5.2 plugs in via Portkey with the `ab_evals` gate. (Rejected: a separate bounded context;
   deferring ideation entirely.)
7. **Console→gateway hop uses a service agent identity + operator in metadata.** The console calls
   under a credential mapped to `growth.experiment_design_agent`; the VULN-001-verified operator id
   is recorded as `maker`/metadata — one governed path, dual attribution — via a `GrowthPort`
   (stub + Http adapter) mirroring `KillSwitchPort`/`ApprovalPort`. (Rejected: operator identity into
   the gateway; console bypassing the gateway.)
8. **LLM scores, deterministic gate.** The Validator emits per-dimension rubric scores (advisory,
   structured output); a pure `ideation_gate` applies the threshold (overall ≥ 3.5 AND novelty ≥ N
   AND grounding ≥ G) → PROCEED/REFINE/KILL, capping un-grounded ideas. Replayable despite model-
   authored scores; mirrors `ab_social` composite scoring + the `ab_evals` promotion gate.

## Determinism & governance (not grilled — inherited)

- Single governed ingress: every experiment-creating call goes through `ab_gateway` (OPA default-
  deny + tool registry + untrusted-input/egress guards + hash-chained audit). Ideation adds no new
  ingress.
- `business_id` is a first-class dimension on the tool, table, event, and OPA input (ADR-0057).
- Ports + stubs at every external seam (LLM, ad/MVP data reads, the gateway hop); infra-free CI.

## Consequences

- The growth context gains persistence and a governed write path for the first time; the console's
  `/experiments` view moves from sample providers to the real table.
- `tenant_id` (doc) is normalized to `business_id`; a new `ExperimentCreated` event joins the
  existing `ExperimentConcluded`.
- A clear, auditable determinism line: idea generation and scores are advisory; the create gate, the
  `decide` verdict, the budget cap, and the ideation threshold are deterministic and replayable.

## Shipped

- **E1 (tracer bullet — `growth.experiment.create`):** `ExperimentCreate`/`Arm` arg models +
  `ExperimentCreated` event (AsyncAPI-documented); an `experiments` table + `ab_growth/store.py`
  (`create`/`get`/`list_open`, idempotent on `experiment_id`, `business_id`-scoped, publishes the
  event on a real insert); `tools.create_experiment` — validate → tenant bind (`authz`) →
  affordability gate (shared `_require_ready_business` + `can_spend`, a read; **no cash moves**) →
  persist → emit; registered in `REGISTRY` (`write`, `sensitive`); OPA rule + `authz` grant for
  `growth.experiment_design_agent` (portfolio-wide, tenant-bound). 8 tests (6 infra-free: two-arm
  rule, event shape, cross-tenant + bad-args denials, governed contract, authz; 2 infra-gated:
  persists without moving cash + tenant-scoped read, affordability denial). Verified live: all 8
  pass against real Postgres, and OPA authorizes the design agent (tenant-bound) while denying other
  principals and the design agent's non-granted actions.

## Rejected / deferred

Ledger earmark of budget; N-arm `decide`; a deterministic Bayesian/sequential test; new registry
agents / LangGraph/CrewAI orchestration. Each is logged in PRD 0007 rather than silently dropped.
