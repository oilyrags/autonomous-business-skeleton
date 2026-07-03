"""Persisted model promotions (PRD 0009 S2 / ADR-0061).

`PromotionRegistry` is in-memory, so a promoted model can only survive by re-evaluating at every
boot. This records a promotion **once** to the `model_promotions` table (audited via `ModelPromoted`)
and hydrates the in-memory registry from it at service startup — so an explicit, eval-gated
`eval-promote` run is a durable, replayable decision, not a per-boot side effect. `business_id`-free
(models are fleet-wide). Persistence + bus; the gate/eval logic stays pure in `ab_evals.gate`.
"""

from __future__ import annotations

from ab_common import bus, db
from ab_common.config import settings
from ab_evals.registry import PromotionRegistry
from ab_schemas.events import ModelPromoted, build


def record(task_profile: str, model_version: str, *, eval_score: float, decided_by: str) -> None:
    """Persist a promotion (a model version cleared to serve a task profile) and publish an audited
    `ModelPromoted`. Append-only — the latest row per profile wins (see `promoted_versions`)."""
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO model_promotions (task_profile, model_version, eval_score, decided_by) "
            "VALUES (%s, %s, %s, %s)",
            (task_profile, model_version, eval_score, decided_by),
        )
        conn.commit()
    event = build(
        ModelPromoted,
        subject=("Model", model_version),
        producer=decided_by,
        task_profile=task_profile,
        model_version=model_version,
        eval_score=eval_score,
    )
    bus.publish_event(settings.model_promoted_topic, key=task_profile, event=event)


def promoted_versions() -> dict[str, str]:
    """The latest promoted model version per task profile (the serving map)."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ON (task_profile) task_profile, model_version "
            "FROM model_promotions ORDER BY task_profile, promoted_at DESC, id DESC"
        ).fetchall()
    return {str(profile): str(version) for profile, version in rows}


def hydrate(registry: PromotionRegistry) -> int:
    """Load persisted promotions into an in-memory `registry` (called at gateway startup). Returns the
    number of profiles hydrated."""
    versions = promoted_versions()
    for profile, version in versions.items():
        registry.promote(profile, version)
    return len(versions)
