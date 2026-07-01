"""Promotion gate: a model version serves a task profile ONLY if it passes the eval
gate (architecture/11 §5). Pass emits ``ModelPromoted``; failure emits
``ModelEvaluationFailed`` and blocks. Never a silent best-guess on a governed path.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from ab_evals.harness import EvalReport, EvalSet, Model, evaluate
from ab_schemas.events import (
    DataClassification,
    ModelEvaluationFailed,
    ModelPromoted,
    SubjectRef,
)

GATE_PRODUCER = "ai_platform.model_ops_agent"


@dataclass(frozen=True)
class PromotionDecision:
    promoted: bool
    report: EvalReport
    reason: str
    # Exactly one of these is set, mirroring the design's ModelPromoted / ModelEvaluationFailed.
    promoted_event: ModelPromoted | None = None
    failed_event: ModelEvaluationFailed | None = None


def _subject(model_version: str) -> SubjectRef:
    return SubjectRef(type="Model", id=model_version)


def gate(report: EvalReport, min_score: float) -> PromotionDecision:
    """Decide promotion from an eval report. Blocks on any critical failure OR a score
    below ``min_score``. Builds the canonical domain event for whichever path taken."""
    now = datetime.now(tz=UTC)
    crit = report.critical_failures
    if crit:
        reason = f"critical eval failure(s): {', '.join(crit)}"
        promoted = False
    elif report.score < min_score:
        reason = f"score {report.score:.2f} < threshold {min_score:.2f}"
        promoted = False
    else:
        reason = f"passed (score {report.score:.2f} >= {min_score:.2f})"
        promoted = True

    if promoted:
        event = ModelPromoted(
            event_name="ModelPromoted",
            event_id=str(uuid.uuid4()),
            occurred_at=now,
            producer=GATE_PRODUCER,
            data_classification=DataClassification.INTERNAL,
            subject_ref=_subject(report.model_version),
            task_profile=report.task_profile,
            model_version=report.model_version,
            eval_score=report.score,
        )
        return PromotionDecision(True, report, reason, promoted_event=event)

    failed = ModelEvaluationFailed(
        event_name="ModelEvaluationFailed",
        event_id=str(uuid.uuid4()),
        occurred_at=now,
        producer=GATE_PRODUCER,
        data_classification=DataClassification.CONFIDENTIAL,
        subject_ref=_subject(report.model_version),
        task_profile=report.task_profile,
        model_version=report.model_version,
        eval_score=report.score,
        failed_cases=list(report.failed_cases),
        reason=reason,
    )
    return PromotionDecision(False, report, reason, failed_event=failed)


def evaluate_and_gate(model: Model, eval_set: EvalSet) -> PromotionDecision:
    """Convenience: run the eval set then apply the gate at the set's threshold."""
    return gate(evaluate(model, eval_set), eval_set.min_score)
