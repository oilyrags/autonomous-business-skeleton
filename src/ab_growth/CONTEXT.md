# Experimentation & Growth

The experimentation engine: given an A/B experiment's evidence and a business Blueprint, decide scale / pivot / kill / continue — deterministically, guardrails first.

## Language

**Experiment**:
A control-vs-variant test with impressions, conversions, and spend per arm; the unit the engine decides on.
_Avoid_: test, trial (informally)

**Blueprint**:
A business's per-instance config (economics, success KPI, guardrails, LLM budget, enabled modules) that scopes its experiments.
_Avoid_: config, template, spec

**Scale / Pivot / Kill / Continue**:
The four experiment outcomes — invest more / iterate / stop / gather more data — decided from significance + guardrails.
_Avoid_: pass/fail, win/lose

**Guardrail Breach**:
A hard-stop condition (e.g. CAC over the ceiling) that forces KILL regardless of statistical significance.
_Avoid_: failure, violation (informally)
