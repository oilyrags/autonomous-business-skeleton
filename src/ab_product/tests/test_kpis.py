"""Product Engineering KPI projections (PRD 0008 P6): per-business fleet metrics + Prometheus gauges.
Pure, infra-free."""

from __future__ import annotations

from ab_product.kpis import ProductKpi, product_gauges, product_kpis
from ab_product.pipeline import PipelineState, Stage


def test_product_kpis_are_computed_per_business() -> None:
    states = [
        PipelineState("i1", "alpha", Stage.DPIA, "awaiting_human"),
        PipelineState("i2", "alpha", Stage.LAUNCHED, "launched"),
        PipelineState("i3", "beta", Stage.QA, "halted"),
        PipelineState("i4", "beta", Stage.SCAFFOLD, "in_progress"),
    ]
    by = {k.business_id: k for k in product_kpis(states)}

    assert by["alpha"].total == 2 and by["alpha"].awaiting_human == 1 and by["alpha"].launched == 1
    assert by["beta"].total == 2 and by["beta"].halted == 1 and by["beta"].launched == 0


def test_product_gauges_are_business_scoped_prometheus_lines() -> None:
    lines = product_gauges([ProductKpi("alpha", total=2, awaiting_human=1, halted=0, launched=1)])
    assert 'ab_product_initiatives{business_id="alpha"} 2' in lines
    assert 'ab_product_awaiting_human{business_id="alpha"} 1' in lines
    assert 'ab_product_launched{business_id="alpha"} 1' in lines
