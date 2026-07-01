---
status: accepted
---

# Experimentation & Growth engine — the revenue-discovery loop

Acting on the consolidated recommendations (P0, "highest leverage": implement Experimentation
& Growth first). The skeleton had a strong deterministic/governance core but no automated loop
to *discover* revenue — idea → experiment → statistical decision → scale/pivot/kill. This adds
that loop in the skeleton's proven style (deterministic engine + events + tests + a `make`
gate), and introduces `business_id` multi-tenancy (P1/P4, "do now, don't retrofit").

## Decisions

- **`ab_growth` context.** An agent may *propose* an experiment; a deterministic engine decides
  what to do with the evidence — LLMs never override the money/guardrail logic.
- **Statistics are stdlib + exact.** `stats.two_proportion_p_value` (normal approximation via
  `math.erf`) with a `min_exposure_per_arm` guard so a huge apparent lift on a handful of users
  is never called significant. No external stats dependency.
- **Blueprint = per-business config (multi-tenancy).** `Blueprint(business_id, name,
  experiment_budget, min_conversion_rate KPI, max_cac guardrail, alpha, min_exposure)`. The same
  `business_id` scopes the decision event — many businesses run side by side.
- **Decision policy (guardrails first, then evidence):**
  1. real CAC above the ceiling → **KILL** (hard stop, regardless of significance);
  2. significant & worse → **KILL**; significant & meets KPI → **SCALE**; significant lift but
     below KPI → **PIVOT** (iterate);
  3. inconclusive & within budget → **CONTINUE**; inconclusive & budget exhausted → **KILL**.
- **`ExperimentConcluded`** event (business-scoped, `ab_schemas`) so downstream contexts
  (portfolio, data) integrate via the bus.
- **`make growth`** demos the engine across two businesses hitting every decision path; in CI.

## Verified

- `make growth` shows SCALE / KILL-on-CAC / PIVOT / KILL-worse / CONTINUE / KILL-budget across
  two `business_id`s. Tests (+15): the z-test matches known values and blocks tiny-sample wins;
  every decision path; the CAC guardrail overrides significance; `Variant` rejects
  conversions > impressions; the event is business-scoped. lint + mypy strict clean.

## Deferred

The rest of the recommendations' P0–P5 (landing-page/MVP generator + deployer, real ad-platform
& payment-rail integrations, a Business Factory that provisions isolated resources, portfolio
capital allocation, `business_id` propagation through *all* existing contexts, per-business LLM
cost budgets). This slice lands the decision core + the multi-tenancy seam those build on.
