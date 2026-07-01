"""DSAR erasure engine (GDPR Art.17 right to erasure), verification failure-injection #5.

Given a data subject, decide — deterministically, from the ``08`` RoPA — which personal-data
elements are erased and which are **retained under legal hold** (Art.17(3)(b): erasure does
not apply where processing is necessary to comply with a legal obligation; e.g. financial
records kept 10y for tax). Retained items are itemized with their lawful basis + retention
policy so the refusal-to-erase is evidenced. This decides the erasure plan; propagating the
actual deletes across live stores is deferred (no customer stores exist in the skeleton yet).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ab_compliance.ropa import load_inventory


@dataclass(frozen=True)
class ErasurePlan:
    subject_id: str
    erased: tuple[str, ...]  # personal data elements tombstoned
    retained_under_hold: tuple[dict[str, Any], ...]  # {dataElement, lawfulBasis, retentionPolicy, reason}

    @property
    def evidenced(self) -> bool:
        """Every retained item carries the basis + policy that justify keeping it."""
        return all(r.get("lawfulBasis") and r.get("retentionPolicy") for r in self.retained_under_hold)


def legal_hold_policies(inventory: dict[str, Any]) -> set[str]:
    """Retention policies that block erasure (their description cites a legal obligation)."""
    return {
        name
        for name, desc in inventory.get("retentionPolicies", {}).items()
        if "legal_obligation" in desc.lower() or "erasure blocked" in desc.lower()
    }


def erasure_plan(subject_id: str, inventory: dict[str, Any] | None = None) -> ErasurePlan:
    """Decide erase-vs-retain for each personal-data element the business holds on a subject."""
    inv = inventory if inventory is not None else load_inventory()
    holds = legal_hold_policies(inv)
    erased: list[str] = []
    retained: list[dict[str, Any]] = []
    for r in inv.get("records", []):
        if r.get("classification") != "personal":
            continue
        el = r.get("dataElement", "<unnamed>")
        basis = r.get("lawfulBasis")
        rp = r.get("retentionPolicy")
        if basis == "legal_obligation" or rp in holds:
            retained.append(
                {
                    "dataElement": el,
                    "lawfulBasis": basis,
                    "retentionPolicy": rp,
                    "reason": "legal hold — erasure blocked by legal obligation (Art.17(3)(b))",
                }
            )
        else:
            erased.append(el)
    return ErasurePlan(subject_id, tuple(erased), tuple(retained))
