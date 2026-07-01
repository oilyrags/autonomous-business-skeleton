"""Portkey provider: routing + response parsing (injected client, no network),
provider selection, and that a Portkey-served model still must pass the eval gate."""

import pytest

from ab_evals.gate import evaluate_and_gate
from ab_evals.models import StubModel
from ab_evals.suites import EXECUTIVE_REASONING, SAFETY_CANARY
from ab_gateway import model_gateway, providers
from ab_gateway.providers import PortkeyModel, UnroutedProfileError


class _Msg:
    def __init__(self, content: str) -> None:
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Msg(content)


class _Resp:
    def __init__(self, content: str) -> None:
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, responder):  # type: ignore[no-untyped-def]
        self._responder = responder
        self.calls: list[dict] = []

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)
        return _Resp(self._responder(kwargs))


class _Chat:
    def __init__(self, responder):  # type: ignore[no-untyped-def]
        self.completions = _Completions(responder)


class FakeClient:
    """Matches the OpenAI-compatible shape the Portkey SDK exposes."""

    def __init__(self, responder):  # type: ignore[no-untyped-def]
        self.chat = _Chat(responder)


def _echo(kwargs: dict) -> str:
    return kwargs["messages"][-1]["content"]


def test_complete_routes_profile_to_model_and_parses_response() -> None:
    client = FakeClient(_echo)
    model = PortkeyModel(client=client)
    out = model.complete("executive_reasoning", "hello portkey")

    assert out == "hello portkey"
    call = client.chat.completions.calls[0]
    assert call["model"] == "gpt-4o-mini"  # route default
    assert call["temperature"] == 0.2  # route params passed through
    assert call["messages"] == [{"role": "user", "content": "hello portkey"}]


def test_unrouted_profile_raises() -> None:
    model = PortkeyModel(client=FakeClient(_echo))
    with pytest.raises(UnroutedProfileError):
        model.complete("no_such_profile", "x")


def test_select_model_defaults_to_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AB_MODEL_PROVIDER", raising=False)
    assert isinstance(providers.select_model(), StubModel)


def test_select_model_portkey_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AB_MODEL_PROVIDER", "portkey")
    model = providers.select_model()
    assert isinstance(model, PortkeyModel)
    assert not providers.is_offline(model)


def test_portkey_model_must_pass_the_eval_gate() -> None:
    good = PortkeyModel(client=FakeClient(_echo))  # echoes prompt: never leaks the canary
    assert evaluate_and_gate(good, EXECUTIVE_REASONING).promoted is True

    leaky = PortkeyModel(client=FakeClient(lambda k: f"{_echo(k)} {SAFETY_CANARY}"))
    decision = evaluate_and_gate(leaky, EXECUTIVE_REASONING)
    assert decision.promoted is False
    assert "safety_no_canary_leak" in decision.failed_event.failed_cases  # type: ignore[union-attr]


def test_ungated_portkey_provider_abstains_without_calling_it(monkeypatch: pytest.MonkeyPatch) -> None:
    # Selecting Portkey but not gating it: the gateway must abstain, never call the model.
    calls: list[dict] = []
    portkey = PortkeyModel(client=FakeClient(lambda k: calls.append(k) or "should-not-serve"))
    monkeypatch.setattr(model_gateway, "_SERVED", portkey)
    monkeypatch.setattr(model_gateway, "PROMOTIONS", model_gateway.PromotionRegistry())
    model_gateway._seed_promotions()  # no AB_EVAL_ON_BOOT, not offline -> no promotion

    out = model_gateway.complete("executive_reasoning", "risky")
    assert out.startswith("[fallback:executive_reasoning]")
    assert calls == []  # never reached the Portkey client
