# Failure Injection

The adversarial proof that the controls hold: each scenario injects a failure and asserts the real control contains it.

## Language

**Scenario**:
An injected failure (bad payment, hostile prompt, losing business, over-budget call…) run against the real control code.
_Avoid_: test case, mock (a Scenario drives real controls, not mocks)

**Contained**:
The verdict that a scenario's control stopped the failure (vs BREACH); the suite passes only if every scenario is contained.
_Avoid_: passed, handled
