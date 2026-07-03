"""The console growth-propose port selection (PRD 0009 S5): default stub, HttpGrowthPort when
AB_GROWTH_PORT_PROVIDER=http. Infra-free — constructing the Http adapter is lazy (no token minted)."""

from __future__ import annotations

from ab_console import app
from ab_console.growth_port import HttpGrowthPort
from ab_growth.proposer import StubExperimentProposer


def test_defaults_to_the_stub_proposer(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AB_GROWTH_PORT_PROVIDER", raising=False)
    assert isinstance(app.growth_port_provider(), StubExperimentProposer)


def test_selects_http_growth_port_when_configured(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AB_GROWTH_PORT_PROVIDER", "http")
    port = app.growth_port_provider()
    assert isinstance(port, HttpGrowthPort)  # constructed without minting a token (lazy)
