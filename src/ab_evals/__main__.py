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


if __name__ == "__main__":
    sys.exit(main())
