# Reliability

Keeps the system dependable: severity-graded incidents, an error budget that freezes releases, and automatic rollback to the last good version.

## Language

**Incident**:
A graded operational failure (by Severity) that triggers a response — rollback, freeze, postmortem, breach assessment.
_Avoid_: outage, bug, issue (informally)

**Error Budget**:
The tolerated failure allowance for an SLO window; exhausting it freezes further releases.
_Avoid_: SLA slack, tolerance

**Rollback**:
Reverting to the last-good version on a severe incident.
_Avoid_: revert, undo (informally)
