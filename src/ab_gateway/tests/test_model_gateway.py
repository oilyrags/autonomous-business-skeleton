"""Unit test (no infra): the stub model is deterministic."""

from ab_gateway import model_gateway


def test_stub_model_is_deterministic() -> None:
    out1 = model_gateway.complete("executive_reasoning", "hello")
    out2 = model_gateway.complete("executive_reasoning", "hello")
    assert out1 == out2
    assert out1 == "[stub:executive_reasoning] hello"
