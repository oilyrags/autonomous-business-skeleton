"""ab_failsim — the failure-injection scenario suite (verification Audit 12).

Each scenario injects a failure and asserts the implemented control *contains* it. Scenarios
whose component does not exist yet (DSAR erasure flow, incident/rollback) are reported as
DEFERRED, not passed — so the suite never overclaims coverage.
"""
