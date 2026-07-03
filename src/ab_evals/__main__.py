"""Promotion-gate CLI (the release gate).

    uv run python -m ab_evals

Gates the release-candidate model (what the gateway serves) against every task-profile
eval set, and self-checks that the gate still has teeth by confirming known-bad candidates
are BLOCKED. Exits non-zero if the release candidate fails a gate, or if a known-bad
candidate is (wrongly) promoted — so CI can't ship a model that fails evals or a gate that
has gone toothless.
"""

from __future__ import annotations

import sys

from ab_evals.gate import evaluate_and_gate
from ab_evals.harness import Model
from ab_evals.models import (
    BiasedModel,
    BrokenModel,
    CompliantModel,
    HallucinatingModel,
    LeakyModel,
    StubModel,
)
from ab_evals.suites import SIGNIFICANT_CUSTOMER_DECISION, SUITES

RELEASE_CANDIDATE: Model = StubModel()
KNOWN_BAD: tuple[Model, ...] = (LeakyModel(), BrokenModel())


def main() -> int:
    ok = True

    print(f"== release candidate: {RELEASE_CANDIDATE.version} ==")
    for profile, eval_set in SUITES.items():
        d = evaluate_and_gate(RELEASE_CANDIDATE, eval_set)
        verdict = "PROMOTE" if d.promoted else "BLOCK"
        print(f"  [{verdict}] {profile}: {d.reason}")
        if not d.promoted:
            ok = False

    print("== gate self-check: known-bad candidates must be blocked ==")
    for model in KNOWN_BAD:
        for profile, eval_set in SUITES.items():
            d = evaluate_and_gate(model, eval_set)
            status = "blocked (good)" if not d.promoted else "PROMOTED (gate is toothless!)"
            print(f"  {model.version} @ {profile}: {status} — {d.reason}")
            if d.promoted:
                ok = False

    # Audit 9 criteria 2 & 3: grounding threshold + Art.22 bias gate on the significant-
    # decision profile. Compliant must promote; a hallucinator and a biased model must block.
    print(f"== Art.22 governance: {SIGNIFICANT_CUSTOMER_DECISION.task_profile} (grounding + bias) ==")
    good = evaluate_and_gate(CompliantModel(), SIGNIFICANT_CUSTOMER_DECISION)
    print(f"  [{'PROMOTE' if good.promoted else 'BLOCK'}] {CompliantModel().version}: {good.reason}")
    ok = ok and good.promoted
    for model in (HallucinatingModel(), BiasedModel()):
        d = evaluate_and_gate(model, SIGNIFICANT_CUSTOMER_DECISION)
        status = "blocked (good)" if not d.promoted else "PROMOTED (gate is toothless!)"
        print(f"  {model.version}: {status} — {d.reason}")
        if d.promoted:
            ok = False

    print("eval gate: PASS" if ok else "eval gate: FAIL")
    return 0 if ok else 1


def promote(task_profile: str) -> int:
    """`python -m ab_evals promote <task_profile>` — evaluate the SERVED model (AB_MODEL_PROVIDER)
    against the profile's eval suite once and, if it passes the gate, record a persisted, audited
    promotion (PRD 0009 S2). Exits non-zero (nothing recorded) if the profile is unknown or the model
    is blocked — the eval gate is never bypassed."""
    from ab_evals import promotion_store
    from ab_gateway import providers

    eval_set = SUITES.get(task_profile)
    if eval_set is None:
        print(f"unknown task profile {task_profile!r}; known: {', '.join(sorted(SUITES))}")
        return 2
    model = providers.select_model()
    decision = evaluate_and_gate(model, eval_set)
    if not decision.promoted:
        print(f"[BLOCK] {model.version} @ {task_profile}: {decision.reason} — not recorded")
        return 1
    promotion_store.record(
        task_profile, model.version, eval_score=decision.report.score, decided_by="ops.eval_promote"
    )
    print(f"[PROMOTED] {model.version} @ {task_profile}: {decision.reason} — recorded + ModelPromoted")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "promote":
        sys.exit(promote(sys.argv[2]))
    sys.exit(main())
