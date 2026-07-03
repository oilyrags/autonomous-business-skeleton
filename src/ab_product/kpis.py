"""Product Engineering KPI projections (PRD 0008 P6): fold the initiatives store into per-business
fleet metrics, rendered as Prometheus gauges via the shared `ab_monitor.prometheus.gauge` helper —
so the console `/metrics` (M5 rail) feeds both the console and Grafana. `business_id`-scoped.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ab_monitor.prometheus import gauge
from ab_product.pipeline import PipelineState


@dataclass(frozen=True)
class ProductKpi:
    business_id: str
    total: int
    awaiting_human: int  # initiatives sitting on a DPIA/launch human gate (actionable)
    halted: int
    launched: int


def product_kpis(states: Iterable[PipelineState]) -> list[ProductKpi]:
    """Per-business product-initiative KPIs, sorted by business_id for determinism."""
    acc: dict[str, dict[str, int]] = {}
    for s in states:
        b = acc.setdefault(s.business_id, {"total": 0, "awaiting_human": 0, "halted": 0, "launched": 0})
        b["total"] += 1
        if s.status in ("awaiting_human", "halted", "launched"):
            b[s.status] += 1
    return [
        ProductKpi(
            business_id=bid,
            total=v["total"],
            awaiting_human=v["awaiting_human"],
            halted=v["halted"],
            launched=v["launched"],
        )
        for bid, v in sorted(acc.items())
    ]


def product_gauges(kpis: Iterable[ProductKpi]) -> list[str]:
    """Render the KPIs as Prometheus gauge lines (business_id-labelled) via the shared renderer."""
    specs = (
        ("ab_product_initiatives", "Product initiatives in the pipeline.", "total"),
        ("ab_product_awaiting_human", "Initiatives on a human (DPIA/launch) gate.", "awaiting_human"),
        ("ab_product_halted", "Initiatives halted by a failed gate.", "halted"),
        ("ab_product_launched", "Products launched.", "launched"),
    )
    kpis = list(kpis)
    lines: list[str] = []
    for name, help_text, attr in specs:
        lines += gauge(name, help_text, [({"business_id": k.business_id}, getattr(k, attr)) for k in kpis])
    return lines
