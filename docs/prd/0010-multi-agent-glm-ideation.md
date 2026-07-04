# PRD 0010 — Multi-agent GLM-5.2 ideation (growth innovates new business ideas)

> Triage: `ready-for-agent`. Source: `autonomous-initiative-pipeline.prompt.md` + `ideate.md` — the
> "GLM-5.2 in multi-agentic mode to innovate new business ideas" intent. Reconciled via
> `/grill-with-docs` (5 decisions). Decisions: ADR-0062 (grilled). Builds on `ab_growth/ideate.py`
> (PRD 0007: `IdeationModel` port + pure `overall_score`/`ideation_gate`), the governed `model_gateway`
> (eval gate + `complete`, `llm_budget` metering), `ab_gateway/model_routes.py` (`TaskRoute`/`ROUTES`),
> the PRD 0009 machinery (`AB_IDEATION_PROVIDER` selection, persisted `eval-promote`, eval suites), and
> the `ab_console` `/growth` E7 workspace. Tracker: no `gh` → issues under `.scratch/ideate/`.

## Problem statement

The growth engine was meant to use **GLM-5.2 in multi-agentic mode** to innovate business ideas. Today
`ideate.py` does a **single** `model.propose()` (one call, N self-scored candidates), and GLM-5.2 isn't
even wired — the gateway serves the deterministic stub, there is no `ideation` route, and `portkey-ai`
is uninstalled. So the ideation is neither GLM-powered nor multi-agent: it can't actually *innovate*,
only stub-generate.

## Solution

A **`MultiAgentIdeationModel`** adapter behind the existing `IdeationModel` port: **3 generator agents**
(distinct lenses) propose in parallel, a **critic** adversarially challenges every candidate, and a
**synthesizer** merges/dedups/refines into the final self-scored candidates — all GLM-5.2 on the single
governed `ideation` profile (eval-gated + `llm_budget`-metered). The pure `ideation_gate` stays the
authoritative decider; the full agent reasoning is captured as an **advisory trace** and surfaced
distinctly in `/growth`. Selected by `AB_IDEATION_PROVIDER=multiagent`; the stub stays the CI default.
Full rationale + rejected alternatives: ADR-0062.

## Grilled decisions (ADR-0062)

1. Topology = generators → critic → synthesizer (fixed, bounded call count).
2. A `MultiAgentIdeationModel` adapter behind the existing `IdeationModel` port (`ideate()` + gate
   unchanged); orchestration pure over an injected agent-call seam so CI is model-free.
3. One model (GLM-5.2) + one `ideation` profile for all roles; cost via `llm_budget` + the fixed count.
4. Roster = 3 generators (market-gap / adjacent-expansion / contrarian) + 1 critic + 1 synthesizer.
5. Full advisory agent trace, surfaced distinctly from the deterministic verdict.

## Slices (vertical, tracer-bullet first)

**M1 — Tracer: the multi-agent adapter (pure orchestration + stub).** `ab_growth/multiagent.py`:
`MultiAgentIdeationModel` implements `IdeationModel.propose` by orchestrating 3 generators → critic →
synthesizer over an injected `agent_call(profile, prompt) -> str` seam (default `model_gateway.complete`);
role personas as prompt templates; parse each role's JSON output; assemble the final `IdeaCandidate`s +
an advisory `AgentTrace`. A `StubAgentCall` (deterministic canned role outputs) keeps CI model-free.
Wire `AB_IDEATION_PROVIDER=multiagent` in the console's ideation selector (extends PRD 0009 S6). Pure
tests: the roster runs in order, the critic's flags reach the synthesizer, malformed role output
degrades safely (drop/skip, never crash), the deterministic gate still decides.

**M2 — GLM-5.2 route + eval-promote.** Add an `ideation` route to `model_routes.py`
(`default_model` = the GLM OpenRouter slug, generous `max_tokens` for a reasoning model); OpenRouter-
direct wiring via env (`AB_PORTKEY_BASE_URL`/key/model or an OpenRouter client). `python -m ab_evals
promote ideation` against the live GLM (paid) records the persisted, audited promotion (PRD 0009 S2);
until then `model_gateway.complete` abstains and the adapter degrades to the stub — so nothing 500s.

**M3 — Advisory agent trace in `/growth`.** Capture the `AgentTrace` on `IdeationResult`; a pure
view-model renders it; the `growth.html` workspace shows a collapsible "agent trace" (each role's
contribution) **visually distinct** from the PROCEED/REFINE/KILL verdict chips (the E7 advisory pattern).

**M4 — Governance + demo + docs.** Confirm each of the 5 agent calls meters to the business's
`llm_spend` and is denied on budget breach (reuse `complete_for_business`/`llm_budget`); a
`make ideate-multiagent` / demo that runs the pipeline on the stub agent (infra-free) end to end;
CONTEXT-MAP + PRD/ADR closure; `PROJECT.md` changelog.

## Determinism boundary (the audit line)

| Deterministic (replayable; may gate) | Advisory (GLM-5.2; never gates) |
|---|---|
| `overall_score`; `ideation_gate` (grounded + bars → PROCEED); the governed `growth.experiment.create` | every generator proposal; the critic's critiques; the synthesizer's merge + the candidates' self-scores; the whole agent trace |

## Out of scope / follow-ups

- Product-engineering multi-agent (that is `ab_product`/PRD 0008 — deterministic scaffold).
- Scheduled/autonomous ideation runs; role-specialized models; a dedicated per-run spend cap.
- Real `GroundingSource` over `ab_data` (the agents ground on whatever `GroundingReport` provides;
  the stub grounding stays until the live `ab_data` grounding lands — a separate slice).

## Success criteria

With GLM-5.2 promoted for `ideation`, an operator triggers ideation in `/growth` and gets **genuinely
innovated** candidates from a bounded, governed, multi-perspective + adversarial GLM-5.2 pipeline —
each agent call eval-gated + metered to the business `llm_budget`, the full reasoning shown as an
advisory trace, and the deterministic `ideation_gate` still the sole decider of PROCEED/REFINE/KILL.
Without a promoted model the pipeline degrades to the stub (no crash). CI stays infra-free + model-free;
ruff + mypy-strict + pytest green; the determinism boundary is intact.
