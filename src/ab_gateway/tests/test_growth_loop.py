"""The full create → run → conclude growth loop (PRD 0007 E3), against real Postgres + bus.
Infra-gated (mirrors the other gateway integration tests); skips cleanly without `make up-infra`."""

from __future__ import annotations

from ab_growth import runner, store
from ab_growth.blueprint import Blueprint
from ab_schemas.models import Arm, ExperimentCreate

_CONTROL = runner.ArmStats(impressions=1_000, conversions=40, spend_minor=30_000)
_VARIANT = runner.ArmStats(impressions=1_000, conversions=120, spend_minor=30_000)  # clear win


def _blueprint() -> Blueprint:
    return Blueprint(
        business_id="rocket",
        name="rocket",
        target_revenue_minor=5_000_000,
        experiment_budget_minor=200_000,
        min_conversion_rate=0.04,
        max_cac_minor=5_000,
    )


def test_create_run_conclude_moves_the_experiment_to_concluded(clean_db: None) -> None:
    proposal = ExperimentCreate(
        business_id="rocket",
        hypothesis="a shorter headline lifts signups",
        arms=[Arm(name="control"), Arm(name="treatment")],
        budget_minor=200_000,
        success_metrics=["activation_rate"],
    )
    store.create(proposal, "exp-loop-1", created_by="growth.experiment_design_agent")
    record = store.get("exp-loop-1")
    assert record is not None and record.status == "proposed"
    assert [r.experiment_id for r in store.list_open("rocket")] == ["exp-loop-1"]  # open

    decision = runner.run(record, _blueprint(), control=_CONTROL, variant=_VARIANT)
    assert decision.action.value == "scale"  # the deterministic verdict on the live stats

    store.conclude(runner.assemble(record, _CONTROL, _VARIANT), decision)
    assert store.get("exp-loop-1").status == "concluded"  # persisted
    assert store.list_open("rocket") == []  # concluded → no longer open


def test_conclude_is_idempotent_and_publishes_the_outcome_once(clean_db: None, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from ab_common.config import settings

    proposal = ExperimentCreate(
        business_id="rocket",
        hypothesis="a shorter headline lifts signups",
        arms=[Arm(name="control"), Arm(name="treatment")],
        budget_minor=200_000,
        success_metrics=["activation_rate"],
    )
    store.create(proposal, "exp-idem-1", created_by="growth.experiment_design_agent")
    record = store.get("exp-idem-1")
    assert record is not None
    exp = runner.assemble(record, _CONTROL, _VARIANT)
    decision = runner.run(record, _blueprint(), control=_CONTROL, variant=_VARIANT)

    published: list[str] = []  # count publishes AFTER create (so only the conclude events)
    # publishing flows through the shared persist_and_emit → bus.publish seam; patch it at the source
    monkeypatch.setattr("ab_common.bus.publish", lambda topic, *, key, value: published.append(topic))

    assert store.conclude(exp, decision) is True  # first call transitions
    assert store.conclude(exp, decision) is False  # already concluded → no-op
    concluded = [t for t in published if t == settings.experiment_concluded_topic]
    assert len(concluded) == 1  # the outcome is published exactly once (no double-count)
