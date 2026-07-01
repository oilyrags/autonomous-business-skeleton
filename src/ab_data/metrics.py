"""Semantic layer: one canonical definition per KPI.

Metrics are defined ONCE in ``REGISTRY``. Registering a name twice raises —
that is the enforced invariant ("every KPI has exactly one canonical definition",
architecture/16 data audit). A metric's SQL runs against the gold/silver models
in the DuckDB warehouse.
"""

from dataclasses import dataclass, field


class DuplicateMetricError(Exception):
    """Raised when a KPI name is defined more than once."""


class UnknownMetricError(Exception):
    """Raised when a metric name is not registered."""


@dataclass(frozen=True)
class Metric:
    name: str
    description: str
    sql: str  # returns a single scalar value
    grain: str


@dataclass
class MetricRegistry:
    _metrics: dict[str, Metric] = field(default_factory=dict)

    def register(self, metric: Metric) -> None:
        if metric.name in self._metrics:
            raise DuplicateMetricError(
                f"KPI {metric.name!r} already defined — exactly one canonical definition is allowed"
            )
        self._metrics[metric.name] = metric

    def get(self, name: str) -> Metric:
        try:
            return self._metrics[name]
        except KeyError as exc:
            raise UnknownMetricError(name) from exc

    def names(self) -> list[str]:
        return sorted(self._metrics)


def _canonical_registry() -> MetricRegistry:
    reg = MetricRegistry()
    reg.register(
        Metric(
            name="decisions_recorded_total",
            description="Total material decisions recorded by agents.",
            sql="SELECT count(*) FROM silver_decisions",
            grain="all-time",
        )
    )
    reg.register(
        Metric(
            name="deciding_agents_total",
            description="Distinct agents that have recorded at least one decision.",
            sql="SELECT count(*) FROM gold_decisions_by_agent",
            grain="all-time",
        )
    )
    return reg


# The single source of truth for KPI definitions.
REGISTRY = _canonical_registry()
