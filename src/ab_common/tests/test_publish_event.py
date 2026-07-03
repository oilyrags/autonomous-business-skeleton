"""`publish_event` is the single place the Envelope→bus wire contract lives: serialize a domain event
to its camelCase wire form and publish it. Infra-free (the bus producer is monkeypatched)."""

from __future__ import annotations

import json

from ab_common import bus
from ab_schemas.events import BusinessActivated, build


def test_publish_event_serializes_camelcase_and_publishes(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(bus, "publish", lambda topic, key, value: calls.append((topic, key, value)))

    event = build(BusinessActivated, subject=("Business", "acme"), producer="p",
                  business_id="acme", name="Acme", capital_minor=1)
    bus.publish_event("business.topic", key="acme", event=event)

    assert len(calls) == 1
    topic, key, value = calls[0]
    assert topic == "business.topic" and key == "acme"
    wire = json.loads(value)
    assert wire["eventName"] == "BusinessActivated"  # camelCase wire aliases
    assert wire["businessId"] == "acme" and wire["subjectRef"] == {"type": "Business", "id": "acme"}
