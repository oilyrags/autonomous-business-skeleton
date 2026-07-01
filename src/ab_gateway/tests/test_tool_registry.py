"""Infra-free: the tool registry contract + the untrusted-input & exfiltration rules."""

from ab_gateway import tools
from ab_schemas.events import DataClassification


def test_registered_tool_has_a_contract() -> None:
    spec = tools.get("decision_registry.write")
    assert spec is not None
    assert spec.side_effect == "write"
    assert spec.sensitive is True


def test_payments_transfer_has_a_sensitive_irreversible_contract() -> None:
    spec = tools.get("payments.transfer")
    assert spec is not None
    assert spec.sensitive is True and spec.side_effect == "irreversible" and spec.egress is False


def test_unregistered_tool_is_uncallable() -> None:
    assert tools.get("nonexistent.tool") is None


def test_sensitive_tool_fails_closed_under_untrusted_input() -> None:
    spec = tools.get("decision_registry.write")
    assert spec is not None
    assert tools.blocked_by_input_trust(spec, untrusted_input=True) is True
    assert tools.blocked_by_input_trust(spec, untrusted_input=False) is False


def test_tools_discovery_endpoint_lists_contracts() -> None:
    from ab_gateway.app import list_tools

    catalog = {t["name"]: t for t in list_tools()}
    assert "decision_registry.write" in catalog
    entry = catalog["decision_registry.write"]
    assert entry["sensitive"] is True and entry["side_effect"] == "write" and entry["description"]


def test_non_sensitive_tool_runs_even_on_untrusted_input() -> None:
    read_tool = tools.ToolSpec(
        name="knowledge.search",
        handler=lambda principal, args: "ok",
        side_effect="read",
        sensitive=False,
        description="read-only",
    )
    assert tools.blocked_by_input_trust(read_tool, untrusted_input=True) is False


def test_egress_tool_blocks_data_above_clearance() -> None:
    egress = tools.get("notify.external")
    assert egress is not None and egress.egress is True
    # clearance is INTERNAL: internal/public pass; confidential/personal/financial are blocked.
    assert tools.exfiltration_blocked(egress, data_classification=DataClassification.INTERNAL) is False
    assert tools.exfiltration_blocked(egress, data_classification=DataClassification.PUBLIC) is False
    assert tools.exfiltration_blocked(egress, data_classification=DataClassification.CONFIDENTIAL) is True
    assert tools.exfiltration_blocked(egress, data_classification=DataClassification.PERSONAL) is True
    assert tools.exfiltration_blocked(egress, data_classification=DataClassification.FINANCIAL) is True


def test_non_egress_tool_is_never_exfiltration_blocked() -> None:
    write = tools.get("decision_registry.write")
    assert write is not None and write.egress is False
    assert tools.exfiltration_blocked(write, data_classification=DataClassification.FINANCIAL) is False
