"""RoPA / lawful-basis compliance gate (Audit 4).

    uv run python -m ab_compliance

Fails (non-zero) if any personal data is processed without a documented lawful basis or a
matching 08 data-inventory record.
"""

from __future__ import annotations

import sys

from ab_compliance.ropa import check


def main() -> int:
    violations = check()
    if violations:
        print(f"compliance gate: FAIL ({len(violations)} violation(s))")
        for msg in violations:
            print(f"  - {msg}")
        return 1
    print("compliance gate: PASS (all personal data has a lawful basis + 08 RoPA record)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
