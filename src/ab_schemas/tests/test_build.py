"""`build()` collapses the six-field envelope ritual every domain event repeats into one call:
event_name (the class name), a fresh event_id, occurred_at, producer, classification, subject_ref —
plus the domain fields. Pure (constructs, never publishes). Infra-free."""

from __future__ import annotations

from datetime import UTC

from ab_schemas.events import BusinessActivated, DataClassification, build


def test_build_fills_the_envelope_from_the_class_and_passes_domain_fields() -> None:
    event = build(
        BusinessActivated,
        subject=("Business", "acme"),
        producer="executive.portfolio_agent",
        business_id="acme",
        name="Acme",
        capital_minor=500_000,
    )

    assert event.event_name == "BusinessActivated"  # derived from the class, not hand-typed
    assert len(event.event_id) == 32 and int(event.event_id, 16) >= 0  # a fresh uuid4 hex
    assert event.occurred_at.tzinfo is UTC  # tz-aware UTC
    assert event.producer == "executive.portfolio_agent"
    assert event.data_classification is DataClassification.INTERNAL  # default
    assert event.subject_ref.type == "Business" and event.subject_ref.id == "acme"
    assert event.business_id == "acme" and event.name == "Acme" and event.capital_minor == 500_000


def test_build_takes_a_classification_override_and_mints_distinct_event_ids() -> None:
    a = build(BusinessActivated, subject=("Business", "b"), producer="p", business_id="b",
              name="B", capital_minor=1, data_classification=DataClassification.FINANCIAL)
    b = build(BusinessActivated, subject=("Business", "b"), producer="p", business_id="b",
              name="B", capital_minor=1, data_classification=DataClassification.FINANCIAL)
    assert a.data_classification is DataClassification.FINANCIAL  # override honoured
    assert a.event_id != b.event_id  # each call is a distinct event
