"""The gated SDLC create → advance → persist loop (PRD 0008 P2), against real Postgres + bus.
Infra-gated (mirrors the growth loop); skips cleanly without `make up-infra`."""

from __future__ import annotations

from ab_product import store
from ab_product.pipeline import GateResult, Stage, advance, approve_human


def test_create_advance_persist_loop_is_business_scoped_and_idempotent(clean_db: None) -> None:
    state = store.create("init-1", "vehicle-twin", "Vehicle Twin")
    assert state.stage is Stage.INTAKE
    assert store.get("init-1") is not None and store.get("init-1").stage is Stage.INTAKE

    store.save(advance(state, GateResult(ok=True)))  # → spec, persisted + published
    assert store.get("init-1").stage is Stage.SPEC

    assert [s.initiative_id for s in store.list_by_business("vehicle-twin")] == ["init-1"]  # tenant-scoped

    store.create("init-1", "vehicle-twin", "Vehicle Twin")  # idempotent — no duplicate row
    assert len(store.list_by_business("vehicle-twin")) == 1


def test_a_human_gate_pauses_the_persisted_initiative(clean_db: None) -> None:
    state = store.create("init-2", "biz", "Biz")
    for _ in range(3):  # intake → spec → design → dpia (human)
        state = advance(state, GateResult(ok=True))
    store.save(state)
    persisted = store.get("init-2")
    assert persisted is not None
    assert persisted.stage is Stage.DPIA and persisted.status == "awaiting_human"

    store.save(approve_human(persisted, actor="dpo"))  # DPIA signed → blueprint
    assert store.get("init-2").stage is Stage.BLUEPRINT
