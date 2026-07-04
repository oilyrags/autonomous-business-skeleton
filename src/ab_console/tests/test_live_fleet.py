"""Live fleet/econ/checks readers (PRD 0009 S4 follow-up): ledger-backed snapshots, unit economics,
and per-business health checks. Infra-free — the factory list + ledger reads are faked."""

from __future__ import annotations

from ab_console import live_reads
from ab_ledger.core import LedgerSpend


def _fake_ledger(monkeypatch, revenue: int, llm: int, external: int) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(live_reads.factory_store, "list_active", lambda: ["rocket"])
    monkeypatch.setattr(live_reads.ledger_store, "business_revenue", lambda bid: revenue)
    monkeypatch.setattr(
        live_reads.ledger_store, "business_spend", lambda bid: LedgerSpend("rocket", llm, external)
    )


def test_snapshots_come_from_the_live_ledger(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _fake_ledger(monkeypatch, revenue=500_000, llm=20_000, external=30_000)
    snaps = live_reads.snapshots()
    assert len(snaps) == 1 and snaps[0].business_id == "rocket"
    assert snaps[0].revenue_minor == 500_000
    assert snaps[0].operating_profit_minor == 450_000  # 500k revenue − 20k llm − 30k ad − 0 cogs


def test_checks_flag_an_operating_loss(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _fake_ledger(monkeypatch, revenue=10_000, llm=50_000, external=0)  # loss
    checks = live_reads.checks()
    assert checks[0].business_id == "rocket"
    assert checks[0].status.name == "CRITICAL"  # operating profit < 0


def test_econ_projects_unit_economics_from_the_ledger(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _fake_ledger(monkeypatch, revenue=500_000, llm=20_000, external=30_000)
    econ = live_reads.econ()
    assert "rocket" in econ and econ["rocket"].business_id == "rocket"


def test_fleet_provider_dispatches_live(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from ab_console import app

    monkeypatch.setattr(app, "_CONSOLE_LIVE", True)
    monkeypatch.setattr(app.live_reads, "fleet", lambda: "LIVE_FLEET")
    assert app.fleet_provider() == "LIVE_FLEET"
