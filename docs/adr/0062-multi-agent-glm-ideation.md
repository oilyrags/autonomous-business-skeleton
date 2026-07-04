---
status: accepted
---

# Multi-agent GLM-5.2 ideation for the growth/experimentation engine

Realizes the "GLM-5.2 in multi-agentic mode to innovate new business ideas" intent of
`autonomous-initiative-pipeline.prompt.md` + `ideate.md`. Today `ab_growth/ideate.py` does a **single**
`IdeationModel.propose(business_id, grounding, count)` — one model call returning N self-scored
`IdeaCandidate`s — and a **pure `ideation_gate`** turns the advisory scores into a replayable
PROCEED/REFINE/KILL verdict (grounding gates PROCEED as an anti-hallucination cap). GLM-5.2 is not
wired (served model is the stub; no `ideation` route; `portkey-ai` uninstalled). Grilled via
`/grill-with-docs`. Plan: PRD 0010.

## Decisions (grilled)

1. **Topology = generators → critic → synthesizer** (a fixed pipeline). N generator agents propose in
   parallel from distinct lenses; a red-team critic adversarially challenges every candidate; a
   synthesizer merges/dedups/refines into the final self-scored candidates. Genuinely multi-perspective
   + adversarial, but a **fixed, bounded** GLM-call count per run (governable cost). Maps onto the
   skeleton's fan-out→verify→synthesize patterns. (Rejected: unbounded debate-until-convergence rounds;
   a single model playing all roles in one prompt — not truly multi-agent.)
2. **A new `MultiAgentIdeationModel` adapter behind the existing `IdeationModel` port.** The
   generator/critic/synthesizer orchestration is hidden behind `propose()`; `ideate()`,
   `overall_score`, and `ideation_gate` are **unchanged**. Selected via `AB_IDEATION_PROVIDER`
   (the PRD 0009 S6 seam): `stub | modelgateway | multiagent`. Ports+stubs preserved —
   `StubIdeationModel` stays the CI default and the orchestration is pure over an injected agent-call
   seam so CI runs model-free. (Rejected: a separate multi-agent module + second port; inlining the
   loop into `ideate()`.)
3. **One model + one `ideation` task profile for every role.** All roles call GLM-5.2 on the single
   `ideation` profile (one OpenRouter route, one eval-promotion, one metering profile); roles differ by
   **persona/prompt only**. Cost is governed by the existing per-business `llm_budget` (every
   `model_gateway.complete` call is metered to the ledger and the gateway denies once a call would
   breach) plus the **fixed** per-run call count → predictable spend. (Rejected: role-specialized
   models/profiles — multiple routes/suites/promotions; a separate per-run cap — the bounded count +
   `llm_budget` already bound it.)
4. **Roster = 3 generators + 1 critic + 1 synthesizer (5 GLM calls/run).** Generator lenses:
   (a) market-gap / underserved-segment, (b) adjacent-expansion from the business's existing strengths,
   (c) contrarian / counter-trend. The critic batch-critiques all candidates in one call (risks,
   duplicates, weak grounding); the synthesizer produces the final scored candidates. Fixed +
   predictable. (Rejected: 2 generators + a combined critic-synth — weaker adversarial separation;
   configurable N — variable cost.)
5. **Full advisory agent trace, surfaced distinctly.** Each role's output — the generators' raw
   proposals, the critic's per-idea risks/dup flags, the synthesizer's merge rationale — is captured as
   advisory metadata on the `IdeationResult` and shown in the `/growth` workspace as a collapsible
   "agent trace", **visually distinct** from the deterministic verdict chips (the E7 pattern), and kept
   for audit. It is **never** fed to the gate. Matches the prompt's "reasoning at every gate."
   (Rejected: summary-only; no trace.)

## Determinism boundary (unchanged, restated)

| Advisory (GLM-5.2 agents; never gates) | Deterministic (replayable; authoritative) |
|---|---|
| every generator's proposals; the critic's critiques; the synthesizer's merge + the candidates' self-scores; the whole agent trace | `overall_score` (mean of the 5 rubric dims); `ideation_gate` (PROCEED needs grounded + overall/novelty/grounding bars); the governed `growth.experiment.create` that a PROCEED idea reaches |

The multi-agent pipeline produces **better-vetted** candidates + scores *before* the gate; the gate is
identical to today. Each agent call routes through the governed `model_gateway` (eval-gated: an
un-promoted model abstains; metered to `llm_budget`).

## GLM-5.2 wiring

GLM-5.2 via **OpenRouter direct** on a new `ideation` route in `ab_gateway/model_routes.py`
(`default_model` = the GLM OpenRouter slug — to be confirmed; "GLM-5.2" is not a standard slug), with a
**generous `max_tokens`** (the routes docstring warns reasoning models return empty content on a small
budget). Promoted for `ideation` via the PRD 0009 S2 `eval-promote` path. Paid external calls, governed
+ metered like any model call.

## Consequences

- The growth engine can genuinely innovate ideas via a bounded, governed, multi-perspective +
  adversarial GLM-5.2 pipeline — without touching the deterministic gate or the ports+stubs CI story.
- Reuses PRD 0009 (per-port selection, persisted eval-promotion, `llm_budget` metering), the E7
  advisory-narrative console pattern, and the existing `IdeationModel` seam — no new framework.
- Cost is bounded + attributable per business; CI stays infra-free and model-free.

## Out of scope / deferred

Product-engineering multi-agent (that is `ab_product`, PRD 0008 — deterministic scaffold); auto-running
ideation on a schedule; role-specialized models; a dedicated per-run budget cap.
