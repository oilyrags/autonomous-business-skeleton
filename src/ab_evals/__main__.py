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
from ab_evals.models import BrokenModel, LeakyModel, StubModel
from ab_evals.suites import SUITES

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

    print("eval gate: PASS" if ok else "eval gate: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
