# Monitoring

Turns the skeleton's existing deterministic signals (service health, `ab_ops` error budgets, `ab_obs`
health, ledger/audit/kill-switch invariants) into Nagios plugin check results, tagged by business_id
and exported through a swappable port. It measures; it does not reinvent the signals.

## Language

**Check**:
A named evaluation of one signal against thresholds, producing a `CheckResult`. Registered as a thunk in the check suite.
_Avoid_: monitor, probe, test (a test verifies code)

**Check Result**:
The Nagios plugin outcome — status (OK/WARNING/CRITICAL/UNKNOWN) + a plugin-output line + perfdata; renders to `STATUS: output | perfdata`.
_Avoid_: alert, health status, reading (informally)

**Check Status**:
The four plugin exit codes: OK=0, WARNING=1, CRITICAL=2, UNKNOWN=3.
_Avoid_: severity (a Severity is the `ab_ops` incident grade), level

**Perfdata**:
A check's machine-readable metrics — `label=value;warn;crit` — for graphing.
_Avoid_: metrics, stats (when you mean the plugin field)

**SLO Burn Rate**:
How fast an `ab_ops` error budget is being consumed; the basis for alerting over raw thresholds.
_Avoid_: error rate, burn (bare)

**Nagios Exporter (port)**:
The seam that renders/submits check results in the plugin protocol; stub by default, NSCA / Icinga2-REST adapters behind it.
_Avoid_: publisher, notifier, sink
