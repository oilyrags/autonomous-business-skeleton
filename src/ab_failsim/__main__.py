"""Failure-injection suite runner (Audit 12).

    uv run python -m ab_failsim

Injects each scenario against the real controls and reports CONTAINED / BREACH / DEFERRED.
Exits non-zero if any non-deferred scenario's control failed to contain the failure.
"""

from __future__ import annotations

import sys

from ab_failsim.scenarios import run_all


def main() -> int:
    results = run_all()
    breaches = [r for r in results if not r.deferred and not r.contained]
    for r in results:
        tag = "DEFERRED" if r.deferred else ("CONTAINED" if r.contained else "BREACH")
        print(f"  [{tag}] {r.name} ({r.control}): {r.detail}")
    contained = sum(1 for r in results if not r.deferred and r.contained)
    deferred = sum(1 for r in results if r.deferred)
    print(f"failure-injection: {contained} contained, {len(breaches)} breach, {deferred} deferred")
    return 1 if breaches else 0


if __name__ == "__main__":
    sys.exit(main())
