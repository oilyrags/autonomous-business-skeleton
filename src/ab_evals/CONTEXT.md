# Evals

The serving boundary for AI: a model version may serve a task profile only after it passes its eval gate, including grounding and bias checks.

## Language

**Eval Gate**:
The pass/fail evaluation a model must clear (score threshold + critical cases) before it may be promoted.
_Avoid_: benchmark, test suite (informally)

**Promotion**:
Recording that a model version may serve a task profile; the gateway abstains for any unpromoted profile.
_Avoid_: release, deployment

**Grounding**:
Constraining generation to retrieved, provenance-bearing sources; abstain when unsupported.
_Avoid_: RAG (RAG is the technique), citation (a citation is the artifact)

**Bias Gate**:
The Art.22 fairness check a model must pass before serving significant decisions.
_Avoid_: fairness test, ethics check
