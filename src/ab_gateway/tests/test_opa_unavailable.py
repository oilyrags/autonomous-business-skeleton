"""An OPA outage fails closed as a typed error the gateway turns into an audited 503 deny (VULN-007),
never an unhandled 500. Infra-free: the transport error is injected."""

from __future__ import annotations

import httpx
import pytest

from ab_gateway import opa


def test_authorize_raises_opa_unavailable_when_opa_cannot_be_reached(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: object, **_kwargs: object) -> object:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(opa.httpx, "post", _boom)
    with pytest.raises(opa.OpaUnavailable):
        opa.authorize("executive.cmo_agent", "payments.transfer", "res", "purpose")


def test_authorize_raises_on_a_5xx_from_opa(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def raise_for_status(self) -> None:
            raise httpx.HTTPStatusError("500", request=httpx.Request("POST", "http://opa"), response=None)  # type: ignore[arg-type]

        def json(self) -> dict[str, object]:
            return {}

    monkeypatch.setattr(opa.httpx, "post", lambda *_a, **_k: _Resp())
    with pytest.raises(opa.OpaUnavailable):
        opa.authorize("executive.cmo_agent", "decision_registry.write", "res", "purpose")
