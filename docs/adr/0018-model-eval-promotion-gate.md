---
status: accepted
---

# Model eval + promotion gate — a model earns the right to serve

First slice of the agent platform (architecture/11 §5) and a build-time proof for
verification Audit 9 ("eval gate blocks a known-bad model"). Until now the gateway routed
every task profile to the stub unconditionally. Now a model version serves a profile only
if it has passed that profile's eval set.

## Decisions

- **`ab_evals` — code-defined eval harness.** Each task profile has an `EvalSet` of cases
  (like the metrics registry: one source of truth in code). A case is a deterministic
  `check` on the candidate's output, tagged with a `dimension` (capability / safety / …)
  and a `critical` flag. No LLM/infra — candidate models are plain callables, so the whole
  gate is deterministic and unit-testable.
- **Hard safety gate.** `gate()` blocks on *any* critical failure regardless of score, and
  otherwise on `score < min_score`. So a single prompt-injection leak blocks promotion even
  if capability is perfect — matching the design's non-negotiable safety gate.
- **Canonical events.** Pass emits `ModelPromoted`, failure emits `ModelEvaluationFailed`
  (both added to `ab_schemas`, per the `04` catalog / `ai_platform` context) carrying the
  score, failed cases, and reason.
- **Serving boundary honours the gate.** `model_gateway` seeds a `PromotionRegistry` at
  import by gating the served model against every suite; `complete()` serves only a promoted
  profile and otherwise returns a deterministic **fallback marker** (never a silent
  best-guess on a governed path). The stub passes `executive_reasoning`, so live behaviour is
  unchanged.
- **CI release gate.** `make eval` gates the release candidate AND self-checks the gate still
  has teeth (known-bad candidates must stay blocked); non-zero exit on either failure. Runs in
  the CI `check` job (pure Python, no infra).

## Verified

- Infra-free tests (+6): good model → promoted + `ModelPromoted` (score 1.0); a
  prompt-injection leaker → **critical block** + `ModelEvaluationFailed` naming
  `safety_no_canary_leak`; a low-capability model → blocked on score; the gateway serves a
  promoted profile and falls back (never silent) for an un-gated one; existing
  `test_model_gateway` still green. `make eval` exits 0 while showing `leaky-0.9` and
  `broken-0.1` blocked. lint + mypy-strict clean.

## Deferred

The other two Audit-9 criteria (grounding-metric threshold; bias/fairness eval wired for
Art.22 profiles); persisting the registry (MLflow/model cards); publishing the eval events
to the bus; wiring real providers (vLLM/managed) — which must pass this same gate to be
promoted.
