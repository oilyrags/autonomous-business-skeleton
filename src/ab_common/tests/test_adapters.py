"""Per-port adapter selection (PRD 0009 S1): AB_<PORT>_PROVIDER picks stub vs a named real adapter,
and a `critical` seam fails closed outside a dev environment. Infra-free."""

from __future__ import annotations

import pytest

from ab_common.adapters import select_adapter


def _stub() -> str:
    return "STUB"


def _real() -> str:
    return "REAL"


def _sel(**kw: object) -> str:
    return select_adapter("myport", stub=_stub, real={"http": _real}, **kw)  # type: ignore[arg-type]


def test_defaults_to_stub_when_unset(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AB_MYPORT_PROVIDER", raising=False)
    assert _sel() == "STUB"


def test_selects_the_named_real_adapter(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AB_MYPORT_PROVIDER", "http")
    assert _sel() == "REAL"


def test_explicit_stub_is_honoured(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AB_MYPORT_PROVIDER", "stub")
    assert _sel() == "STUB"


def test_unknown_provider_raises(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AB_MYPORT_PROVIDER", "bogus")
    with pytest.raises(RuntimeError, match="not a known provider"):
        _sel()


def test_critical_port_fails_closed_outside_dev(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AB_MYPORT_PROVIDER", raising=False)
    monkeypatch.setenv("AB_ENV", "prod")
    with pytest.raises(RuntimeError, match="must select a real adapter"):
        _sel(critical=True)


def test_critical_port_allows_stub_in_dev(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AB_MYPORT_PROVIDER", raising=False)
    monkeypatch.setenv("AB_ENV", "dev")
    assert _sel(critical=True) == "STUB"  # dev may run on the stub


def test_critical_port_in_prod_is_fine_when_real_selected(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AB_ENV", "prod")
    monkeypatch.setenv("AB_MYPORT_PROVIDER", "http")
    assert _sel(critical=True) == "REAL"  # explicit real adapter satisfies fail-closed
