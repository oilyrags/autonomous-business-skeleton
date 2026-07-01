"""Contract tests: the Pydantic event models and the AsyncAPI spec must not drift.

Every domain event has two representations — the Python model that producers construct
(`ab_schemas.events`) and the published contract (`architecture/events.asyncapi.yaml`) that
consumers code against. If they drift, a producer emits a field no consumer expects (or omits one
they require). These tests pin the two together: every model is documented, and its wire fields
match the documented payload exactly. Pure, infra-free.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from ab_schemas.events import Envelope

_SPEC_PATH = Path(__file__).resolve().parents[3] / "architecture" / "events.asyncapi.yaml"
_SPEC: dict[str, Any] = yaml.safe_load(_SPEC_PATH.read_text())
_MESSAGES: dict[str, Any] = _SPEC["components"]["messages"]
_EVENT_MODELS = sorted(Envelope.__subclasses__(), key=lambda c: c.__name__)


def _wire_fields(model: type[Envelope]) -> set[str]:
    """The event-specific wire (camelCase) field names — the model's own fields, minus the
    common Envelope fields (which the spec factors into the shared Envelope schema)."""
    own = set(model.model_fields) - set(Envelope.model_fields)
    return {model.model_fields[name].alias or name for name in own}


def _payload_properties(message: dict[str, Any]) -> set[str]:
    """The properties declared in a message payload's inline object blocks (i.e. excluding the
    shared Envelope `$ref`), across the whole allOf composition."""
    props: set[str] = set()
    for block in message["payload"]["allOf"]:
        if isinstance(block, dict) and block.get("type") == "object":
            props |= set(block.get("properties", {}))
    return props


@pytest.mark.parametrize("model", _EVENT_MODELS, ids=lambda m: m.__name__)
def test_every_event_model_is_documented_in_the_spec(model: type[Envelope]) -> None:
    assert model.__name__ in _MESSAGES, f"{model.__name__} has no AsyncAPI message — undocumented event"


@pytest.mark.parametrize("model", _EVENT_MODELS, ids=lambda m: m.__name__)
def test_model_wire_fields_match_the_documented_payload(model: type[Envelope]) -> None:
    message = _MESSAGES[model.__name__]
    assert _wire_fields(model) == _payload_properties(message), (
        f"{model.__name__}: model fields and AsyncAPI payload have drifted"
    )


@pytest.mark.parametrize("model", _EVENT_MODELS, ids=lambda m: m.__name__)
def test_documented_required_fields_are_actually_required_on_the_model(model: type[Envelope]) -> None:
    # Anything the contract marks `required` must be a non-optional field on the model, so a
    # producer cannot omit what consumers rely on.
    message = _MESSAGES[model.__name__]
    required: set[str] = set()
    for block in message["payload"]["allOf"]:
        if isinstance(block, dict) and block.get("type") == "object":
            required |= set(block.get("required", []))
    alias_to_field = {model.model_fields[n].alias or n: n for n in model.model_fields}
    for wire_name in required:
        field = model.model_fields[alias_to_field[wire_name]]
        assert field.is_required(), f"{model.__name__}.{wire_name} is documented required but optional"
