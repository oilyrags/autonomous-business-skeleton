"""Console live read providers (PRD 0009 S4): the store-backed panels map live records to view-rows;
the AB_CONSOLE_PROVIDER flag dispatches live vs sample. Infra-free (stores faked)."""

from __future__ import annotations

from ab_console import live_reads
from ab_growth.store import ExperimentRecord


def test_experiments_maps_records_to_rows(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    rec = ExperimentRecord(
        experiment_id="exp1",
        business_id="rocket",
        hypothesis="h",
        arm_names=["control", "treatment"],
        budget_minor=1000,
        status="concluded",
        decision="scale",
    )
    monkeypatch.setattr(live_reads.growth_store, "list_by_business", lambda: [rec])

    rows = live_reads.experiments()

    assert len(rows) == 1
    assert rows[0].experiment_id == "exp1" and rows[0].business_id == "rocket"
    assert rows[0].action == "scale"  # concluded decision surfaces as the action


def test_open_experiment_shows_continue(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    rec = ExperimentRecord("exp2", "beacon", "h", ["a", "b"], 1000, "proposed", None)
    monkeypatch.setattr(live_reads.growth_store, "list_by_business", lambda: [rec])
    assert live_reads.experiments()[0].action == "continue"  # no decision yet


def test_provider_dispatches_on_the_console_flag(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from ab_console import app

    monkeypatch.setattr(app, "_CONSOLE_LIVE", True)
    monkeypatch.setattr(app.live_reads, "experiments", lambda: ["LIVE"])
    assert app.experiments_provider() == ["LIVE"]

    monkeypatch.setattr(app, "_CONSOLE_LIVE", False)
    assert app.experiments_provider() is app._SAMPLE_EXPERIMENTS  # sample by default
