"""ab_ops — the Reliability/SRE context: error budgets, release freeze, auto-rollback.

Deterministic controls for the incident failure-injection scenario (architecture/03 QA, 10):
a Sev1 during a release auto-rolls-back to the last good version, freezes further releases
(error-budget / change freeze), requires a postmortem, and — if PII was touched — a breach
assessment.
"""
