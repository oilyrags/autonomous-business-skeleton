"""DSAR erasure engine: erasure propagates but legal-hold records are retained + evidenced."""

from ab_compliance.dsar import ErasurePlan, erasure_plan, legal_hold_policies

_INV = {
    "retentionPolicies": {
        "contact_retention": "Active + 24 months, then erase.",
        "financial_retention": "10 years (legal_obligation — tax). Erasure blocked by legal basis.",
        "dsar_retention": "Proof of fulfilment kept 6 years.",
    },
    "records": [
        {
            "dataElement": "customer.email",
            "classification": "personal",
            "lawfulBasis": "consent",
            "retentionPolicy": "contact_retention",
        },
        {
            "dataElement": "account.billing_contact",
            "classification": "personal",
            "lawfulBasis": "contract",
            "retentionPolicy": "financial_retention",
        },
        {
            "dataElement": "dsar.subject_identity",
            "classification": "personal",
            "lawfulBasis": "legal_obligation",
            "retentionPolicy": "dsar_retention",
        },
        {
            "dataElement": "decision.id",
            "classification": "confidential",
            "retentionPolicy": "contact_retention",
        },
    ],
}


def test_legal_hold_detected_from_description() -> None:
    assert legal_hold_policies(_INV) == {"financial_retention"}


def test_erasure_propagates_but_retains_legal_hold() -> None:
    plan = erasure_plan("subject-1", inventory=_INV)
    assert "customer.email" in plan.erased  # consent-based personal data is erased
    assert "decision.id" not in plan.erased  # non-personal is out of scope
    retained = {r["dataElement"] for r in plan.retained_under_hold}
    assert retained == {
        "account.billing_contact",
        "dsar.subject_identity",
    }  # financial hold + legal_obligation
    assert plan.evidenced is True


def test_real_inventory_yields_a_financial_legal_hold() -> None:
    plan = erasure_plan("subject-1")  # ships-real 08 inventory
    assert plan.erased  # something is erasable
    assert any(r["retentionPolicy"] == "financial_retention" for r in plan.retained_under_hold)
    assert plan.evidenced is True


def test_not_evidenced_when_a_retained_record_lacks_basis() -> None:
    plan = ErasurePlan("s", erased=(), retained_under_hold=({"dataElement": "x", "retentionPolicy": "p"},))
    assert plan.evidenced is False
