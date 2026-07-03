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

**Experiment Proposal**:
A persisted, governed request to run an experiment (business_id, hypothesis, arms, budget cap, success metrics, status), created through the governed `growth.experiment.create` tool. Status flows proposed → running → concluded.
_Avoid_: ticket, request (informally)

**Arm**:
A named variant of the experience (control, treatment…) with optional implementation params; 2–5 per proposal. The control/variant pair is what `decide` scores.
_Avoid_: bucket, cell

**Budget Cap**:
The maximum ad/LLM spend an experiment may incur, checked for affordability at creation but not moved as cash — real spend flows through the existing ledger rails, enforced against the cap by the runner.
_Avoid_: reserve, escrow (no earmark yet — see PRD 0007)

**Idea Candidate**:
A scored, grounded, experiment-ready concept — the ideation engine's unit of output; carries an embedded experiment proposal.
_Avoid_: suggestion, brainstorm

**Advisory Narrative**:
LLM-authored explanation attached to a proposal or outcome; never gates money and is always separated from the deterministic verdict.
_Avoid_: analysis, decision (it is neither authoritative nor a decision)

**Ideation Gate**:
The pure function turning rubric scores → PROCEED / REFINE / KILL (overall ≥ 3.5 + novelty/grounding floors); replayable though the scores are model output.
_Avoid_: filter, review (informally)
