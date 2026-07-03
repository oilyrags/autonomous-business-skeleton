"""The gated SDLC create → advance → persist loop (PRD 0008 P2), against real Postgres + bus.
Infra-gated (mirrors the growth loop); skips cleanly without `make up-infra`."""

from __future__ import annotations

import pytest

from ab_product import store
from ab_product.compliance import clear_dpia
from ab_product.pipeline import GateResult, Stage, advance, approve_human
from ab_schemas.models import ProductInitiative


def test_create_advance_persist_loop_is_business_scoped_and_idempotent(clean_db: None) -> None:
    state = store.create("init-1", "vehicle-twin", "Vehicle Twin")
    assert state.stage is Stage.INTAKE
    assert store.get("init-1") is not None and store.get("init-1").stage is Stage.INTAKE

    spec = advance(state, GateResult(ok=True))
    assert store.save(spec) is True  # → spec, persisted + published on a real transition
    assert store.save(spec) is False  # re-saving the same state is a no-op — no duplicate event
    assert store.get("init-1").stage is Stage.SPEC

    assert [s.initiative_id for s in store.list_by_business("vehicle-twin")] == ["init-1"]  # tenant-scoped

    store.create("init-1", "vehicle-twin", "Vehicle Twin")  # idempotent — no duplicate row
    assert len(store.list_by_business("vehicle-twin")) == 1


def test_a_personal_data_gate_pauses_the_persisted_initiative(clean_db: None) -> None:
    initiative = ProductInitiative(
        initiative_id="init-2", title="Biz", key_features=["store customer records"]
    )  # personal data → DPIA required
    state = store.create("init-2", "biz", "Biz")
    for _ in range(3):  # intake → spec → design → dpia (human)
        state = advance(state, GateResult(ok=True))
    store.save(state)
    persisted = store.get("init-2")
    assert persisted is not None
    assert persisted.stage is Stage.DPIA and persisted.status == "awaiting_human"

    # a plain approval cannot clear a DPIA gate — it must run the compliance check
    with pytest.raises(ValueError, match="clear_dpia"):
        approve_human(persisted, actor="operator")

    store.save(clear_dpia(persisted, initiative, approver="dpo"))  # DPIA signed → blueprint
    assert store.get("init-2").stage is Stage.BLUEPRINT
