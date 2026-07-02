"""Prometheus text exposition (pure): the same deterministic checks and business reads that feed
Nagios, rendered as Prometheus gauges — one definition per signal, two consumers. Hand-rolled
because the exposition format is three trivial line shapes; no `prometheus-client` (and no OTel SDK)
dependency enters the services. Scraped by the monitoring compose profile's Prometheus.
"""

from __future__ import annotations

from collections.abc import Iterable

from ab_monitor.check import CheckResult
from ab_obs.core import BusinessSnapshot, fleet_totals


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _num(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _labels(**labels: str | None) -> str:
    parts = [f'{k}="{_esc(v)}"' for k, v in labels.items() if v]
    return "{" + ",".join(parts) + "}" if parts else ""


def check_metrics(results: Iterable[CheckResult]) -> list[str]:
    """Checks as gauges: status (0 OK / 1 WARNING / 2 CRITICAL / 3 UNKNOWN) + perfdata + thresholds."""
    lines = [
        "# HELP ab_check_status Monitor check status (0 OK, 1 WARNING, 2 CRITICAL, 3 UNKNOWN).",
        "# TYPE ab_check_status gauge",
    ]
    perf: list[str] = []
    warn: list[str] = []
    crit: list[str] = []
    for r in results:
        lines.append(f"ab_check_status{_labels(check=r.name, business_id=r.business_id)} {int(r.status)}")
        for p in r.perfdata:
            labels = _labels(check=r.name, label=p.label, business_id=r.business_id)
            perf.append(f"ab_check_perfdata{labels} {_num(p.value)}")
            if p.warn is not None:
                warn.append(f"ab_check_perfdata_warn{labels} {_num(p.warn)}")
            if p.crit is not None:
                crit.append(f"ab_check_perfdata_crit{labels} {_num(p.crit)}")
    if perf:
        lines += [
            "# HELP ab_check_perfdata Check performance data (the Nagios perfdata value).",
            "# TYPE ab_check_perfdata gauge",
            *perf,
        ]
    if warn:
        lines += ["# TYPE ab_check_perfdata_warn gauge", *warn]
    if crit:
        lines += ["# TYPE ab_check_perfdata_crit gauge", *crit]
    return lines


def business_metrics(snapshots: list[BusinessSnapshot]) -> list[str]:
    """Per-business + fleet economics as gauges (integer minor units / bps), tagged business_id."""
    lines: list[str] = []
    gauges = (
        ("ab_business_revenue_minor", "Revenue attributed to the business (minor units)."),
        ("ab_business_operating_profit_minor", "Operating profit (minor units)."),
        ("ab_business_llm_spend_minor", "LLM inference spend (minor units)."),
        ("ab_business_ad_spend_minor", "Ad spend (minor units)."),
    )
    values = {
        "ab_business_revenue_minor": lambda s: s.revenue_minor,
        "ab_business_operating_profit_minor": lambda s: s.operating_profit_minor,
        "ab_business_llm_spend_minor": lambda s: s.llm_spend_minor,
        "ab_business_ad_spend_minor": lambda s: s.ad_spend_minor,
    }
    for name, help_text in gauges:
        lines += [f"# HELP {name} {help_text}", f"# TYPE {name} gauge"]
        lines += [f"{name}{_labels(business_id=s.business_id)} {values[name](s)}" for s in snapshots]
    ratio = [
        f"ab_business_llm_cost_ratio_bps{_labels(business_id=s.business_id)} {s.llm_cost_ratio_bps}"
        for s in snapshots
        if s.llm_cost_ratio_bps is not None
    ]
    if ratio:
        lines += ["# TYPE ab_business_llm_cost_ratio_bps gauge", *ratio]
    totals = fleet_totals(snapshots)
    lines += [
        "# TYPE ab_fleet_businesses gauge",
        f"ab_fleet_businesses {totals.businesses}",
        "# TYPE ab_fleet_operating_profit_minor gauge",
        f"ab_fleet_operating_profit_minor {totals.total_operating_profit_minor}",
        "# TYPE ab_fleet_unprofitable gauge",
        f"ab_fleet_unprofitable {totals.unprofitable}",
    ]
    return lines


def exposition(results: Iterable[CheckResult], snapshots: list[BusinessSnapshot]) -> str:
    """The full /metrics payload, newline-terminated (Prometheus text format 0.0.4)."""
    return "\n".join(check_metrics(results) + business_metrics(snapshots)) + "\n"


CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"
