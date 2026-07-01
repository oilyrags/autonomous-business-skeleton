"""The revenue rail port: an external payment processor (Stripe / Lemon Squeezy) as a swappable
seam. The stub returns configured charges; a real adapter fetching settled charges from the
processor's API slots in behind the same Protocol — callers (``record_charges``) never change.
"""

from __future__ import annotations

from typing import Protocol

from ab_revenue.core import Charge


class RevenueGateway(Protocol):
    """The slice of a payment processor we depend on: the charges that have settled to money."""

    def settled_charges(self) -> list[Charge]: ...


class StubRevenueGateway:
    """Deterministic in-memory rail for tests + the demo. A real Stripe/Lemon Squeezy adapter
    implements the same ``settled_charges`` by calling the processor API."""

    def __init__(self, charges: list[Charge]) -> None:
        self._charges = list(charges)

    def settled_charges(self) -> list[Charge]:
        return list(self._charges)
