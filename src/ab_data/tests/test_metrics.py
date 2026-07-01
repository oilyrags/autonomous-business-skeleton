"""The semantic-layer invariant: exactly one canonical definition per KPI."""

import pytest

from ab_data.metrics import REGISTRY, DuplicateMetricError, Metric, MetricRegistry, UnknownMetricError


def test_duplicate_kpi_definition_is_rejected() -> None:
    reg = MetricRegistry()
    reg.register(Metric("revenue", "d", "SELECT 1", "all-time"))
    with pytest.raises(DuplicateMetricError):
        reg.register(Metric("revenue", "a different definition", "SELECT 2", "all-time"))


def test_unknown_metric_raises() -> None:
    with pytest.raises(UnknownMetricError):
        MetricRegistry().get("nope")


def test_canonical_registry_definitions_are_unique() -> None:
    # REGISTRY was built at import time without raising => every KPI is defined once.
    names = REGISTRY.names()
    assert "decisions_recorded_total" in names
    assert len(names) == len(set(names))
