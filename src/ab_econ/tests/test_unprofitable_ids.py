"""unprofitable_ids selects the businesses allocation must not fund (pure)."""

from __future__ import annotations

from ab_econ.core import UnitInputs, economics, unprofitable_ids


def _econ(bid: str, *, revenue: int) -> object:
    return economics(
        UnitInputs(
            business_id=bid,
            revenue_minor=revenue,
            cogs_minor=100_000,
            ad_spend_minor=100_000,
            llm_spend_minor=100_000,
            customers=50,
        )
    )


def test_selects_only_unprofitable_businesses() -> None:
    healthy = _econ("healthy", revenue=1_000_000)  # profit +700_000
    bleeder = _econ("bleeder", revenue=200_000)  # profit −100_000
    assert unprofitable_ids([healthy, bleeder]) == {"bleeder"}  # type: ignore[list-item]


def test_empty_when_all_healthy() -> None:
    assert unprofitable_ids([_econ("a", revenue=1_000_000)]) == set()  # type: ignore[list-item]
