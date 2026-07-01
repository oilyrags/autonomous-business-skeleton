"""The gateway's serving boundary honours the eval gate (no ungated model served)."""

from ab_gateway import model_gateway


def test_promoted_profile_is_served() -> None:
    # executive_reasoning's stub passes its eval set at import, so it is promoted.
    assert model_gateway.PROMOTIONS.is_promoted("executive_reasoning")
    assert model_gateway.complete("executive_reasoning", "hello") == "[stub:executive_reasoning] hello"


def test_ungated_profile_falls_back_never_silent_guess() -> None:
    out = model_gateway.complete("unknown_profile", "do something risky")
    assert out.startswith("[fallback:unknown_profile]")
    assert "abstain" in out
