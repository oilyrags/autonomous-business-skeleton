"""LedgerEntryPosted carries an optional business_id on the wire as camelCase businessId."""

from __future__ import annotations

from datetime import UTC, datetime

from ab_schemas.events import DataClassification, LedgerEntryPosted, SubjectRef


def _entry(**over: object) -> LedgerEntryPosted:
    base: dict[str, object] = dict(
        event_name="LedgerEntryPosted",
        event_id="e1",
        occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
        producer="executive.cmo_agent",
        data_classification=DataClassification.FINANCIAL,
        subject_ref=SubjectRef(type="LedgerTransaction", id="txn_1"),
        txn_id="txn_1",
        idempotency_key="k1",
        amount_minor=40_000,
        currency="EUR",
        payee="acme",
        maker="executive.cmo_agent",
    )
    base.update(over)
    return LedgerEntryPosted(**base)  # type: ignore[arg-type]


def test_business_id_defaults_to_none() -> None:
    assert _entry().business_id is None


def test_business_id_serializes_as_camel_case_and_round_trips() -> None:
    entry = _entry(business_id="acme")
    dumped = entry.model_dump_json(by_alias=True)
    assert '"businessId":"acme"' in dumped.replace(" ", "")
    assert LedgerEntryPosted.model_validate_json(dumped).business_id == "acme"
