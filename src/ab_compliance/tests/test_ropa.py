"""Audit 4: the RoPA / lawful-basis compliance gate. Real artifacts pass; each violation
type is caught (failure-injection)."""

from ab_compliance.ropa import check

_POLICIES = {"retentionPolicies": {"r1": "keep a while"}}


def test_real_artifacts_are_compliant() -> None:
    # The shipped 08 inventory + 04 catalog + code inventory must pass with no violations.
    assert check() == []


def test_personal_record_without_lawful_basis_is_flagged() -> None:
    inv = {
        **_POLICIES,
        "records": [{"dataElement": "x.email", "classification": "personal", "retentionPolicy": "r1"}],
    }
    v = check(inventory=inv, code_inventory=[], events=[])
    assert any("no lawfulBasis" in m for m in v)


def test_compliant_personal_record_passes() -> None:
    inv = {
        **_POLICIES,
        "records": [
            {
                "dataElement": "x.email",
                "classification": "personal",
                "lawfulBasis": "consent",
                "retentionPolicy": "r1",
            }
        ],
    }
    assert check(inventory=inv, code_inventory=[], events=[]) == []


def test_undefined_retention_policy_is_flagged() -> None:
    inv = {
        "retentionPolicies": {},
        "records": [{"dataElement": "a", "classification": "internal", "retentionPolicy": "ghost"}],
    }
    v = check(inventory=inv, code_inventory=[], events=[])
    assert any("undefined" in m for m in v)


def test_code_inventory_personal_element_without_ropa_record_is_flagged() -> None:
    inv = {**_POLICIES, "records": []}
    code = [{"dataElement": "y.ssn", "classification": "personal", "retentionPolicy": "r1"}]
    v = check(inventory=inv, code_inventory=code, events=[])
    assert any("no 08 RoPA record" in m for m in v)


def test_personal_event_without_any_basis_is_flagged() -> None:
    inv = {**_POLICIES, "records": []}  # no basis-bearing record backs retention r1
    events = [
        {"event": "MysteryEvent", "cls": "personal", "personal_dsar": "DSAR: access", "retention": "r1"}
    ]
    v = check(inventory=inv, code_inventory=[], events=events)
    assert any("MysteryEvent" in m and "lawful basis" in m for m in v)


def test_personal_event_basis_via_linked_ropa_record_passes() -> None:
    # Event restates no inline basis, but its retention is backed by a personal 08 record
    # that has a lawful basis -> compliant (basis documented at the RoPA level).
    inv = {
        **_POLICIES,
        "records": [
            {
                "dataElement": "dsar.id",
                "classification": "personal",
                "lawfulBasis": "legal_obligation",
                "retentionPolicy": "r1",
            }
        ],
    }
    events = [
        {
            "event": "DataExportCompleted",
            "cls": "personal",
            "personal_dsar": "DSAR: access",
            "retention": "r1",
        }
    ]
    assert check(inventory=inv, code_inventory=[], events=events) == []
