---
status: accepted
---

# Grounding threshold + Art.22 bias eval — closing Audit 9

ADR-0018 shipped the eval/promotion gate and closed the first of verification Audit 9's
three build-time criteria. This slice closes the other two (architecture/11 §4–5): a
**per-profile grounding threshold** and a **bias/fairness eval wired for GDPR Art.22
significant-decision profiles**.

## Decisions

- **Per-dimension thresholds.** `EvalSet` gains `thresholds: {dimension -> min pass-rate}`;
  the gate blocks if any dimension is below its threshold (in addition to critical failures
  and the overall `min_score`). Grounding is just a dimension with a `1.0` threshold — "the
  grounding metric is tracked per task profile and below-threshold blocks the profile."
- **Fairness is a paired (metamorphic) case.** Bias can only be judged by *comparing*
  outputs across protected-attribute groups, so `FairnessCase` prompts the model once per
  `group` (same scenario otherwise) and checks the decision is invariant. It runs alongside
  the single-output `EvalCase`s in `evaluate()`.
- **Art.22 requires a bias eval — enforced.** `EvalSet.art22_significant=True` marks a
  significant-automated-decision profile; the gate **blocks** such a profile if its report
  has no `bias` dimension at all. So you cannot promote an Art.22 model without a fairness
  eval — the wiring is a gate invariant, not a convention.
- **New profile `significant_customer_decision`** (Art.22, customer-facing) carries grounding
  cases (cite-when-supported / abstain-when-unsupported) and a fairness case (approve/deny
  invariant to group). It is a *governance* suite proven by the gate; it joins the served
  `SUITES` once a customer-facing serving path and its promoted model exist (kept out for now
  so the release gate stays about what the gateway actually serves).
- **Reference behaviours** as fixtures: `CompliantModel` (grounds + is fair → promoted),
  `HallucinatingModel` (fabricates → grounding 0.0, blocked), `BiasedModel` (grounds fine but
  decides by group → bias 0.0, blocked). The determinism boundary still holds — these prove
  the *gate*, not a real LLM.

## Verified

- Infra-free tests (+5) and `make eval`: compliant model promoted (grounding 1.0, bias 1.0);
  hallucinator blocked on the grounding threshold (and names `ground_abstain_unsupported`);
  biased model blocked on the bias threshold while grounding stays 1.0 (block attributable to
  bias only); an Art.22 profile lacking a bias eval is rejected with an "Art.22 … requires a
  bias/fairness eval" reason. ADR-0018 tests (safety/capability gating, gateway serving) still
  green; lint + mypy-strict clean.
- `architecture/16` Audit 9 → **PASS (build-proven)**; CONDITIONAL count 5 → 4.

## Deferred

Real grounding via retrieval over approved KnowledgeArtifacts (this uses a minimal
keyword-overlap policy to exercise the gate); richer bias metrics (equalized-odds etc.) and
larger fairness cohorts; serving the Art.22 profile end-to-end through the gateway; emitting
the eval events to the bus / model cards.
