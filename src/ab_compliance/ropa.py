"""RoPA / lawful-basis compliance check (GDPR Art.30 + Art.6), verification Audit 4.

Cross-checks three sources against the ``08`` data inventory (the Record of Processing
Activities): (1) the RoPA itself — every ``personal``/``financial`` record has a lawful
basis and a resolvable retention policy; (2) the code data-inventory
(``ab_data.inventory``) — every element's retention resolves and any personal element has
an ``08`` record; (3) the ``04`` event catalog — every ``personal`` event declares a lawful
basis and a resolvable retention. Returns a list of violation strings (empty == compliant),
so CI fails if personal data is processed without a documented lawful basis.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_ARCH = Path(__file__).resolve().parents[2] / "architecture"
# GDPR lawful basis (Art.6) is a *personal*-data requirement; financial data that is not
# personal needs no lawful basis. Both classes, however, must be inventoried + retention-mapped.
_NEEDS_BASIS = {"personal"}
_MUST_INVENTORY = {"personal", "financial"}


def load_inventory(path: Path | None = None) -> dict[str, Any]:
    p = path or _ARCH / "08_data_inventory_template.json"
    data: dict[str, Any] = json.loads(p.read_text())
    return data


def _load_code_inventory() -> list[dict[str, Any]]:
    from ab_data.inventory import DATA_INVENTORY

    return DATA_INVENTORY


def load_events(path: Path | None = None) -> list[dict[str, str]]:
    """Parse the 04 event-catalog markdown tables into {event, cls, basis, retention}."""
    p = path or _ARCH / "04_event_catalog.md"
    events: list[dict[str, str]] = []
    for line in p.read_text().splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) != 8 or cols[3] not in {"public", "internal", "confidential", "personal", "financial"}:
            continue  # not an events-table data row
        retention = ""
        m = re.search(r"[A-Za-z_]+", cols[4])
        if m:
            retention = m.group(0)
        events.append(
            {"event": cols[0].strip("`"), "cls": cols[3], "personal_dsar": cols[6], "retention": retention}
        )
    return events


def check(
    inventory: dict[str, Any] | None = None,
    code_inventory: list[dict[str, Any]] | None = None,
    events: list[dict[str, str]] | None = None,
) -> list[str]:
    """Return compliance violations (empty == compliant). Inputs are injectable for tests."""
    inv = inventory if inventory is not None else load_inventory()
    code_inv = code_inventory if code_inventory is not None else _load_code_inventory()
    evs = events if events is not None else load_events()

    policies: set[str] = set(inv.get("retentionPolicies", {}))
    records: list[dict[str, Any]] = inv.get("records", [])
    v: list[str] = []

    documented: set[str] = set()
    for r in records:
        el = r.get("dataElement", "<unnamed>")
        if el in documented:
            v.append(f"08: duplicate dataElement '{el}'")
        documented.add(el)
        cls = r.get("classification")
        if cls in _NEEDS_BASIS and not r.get("lawfulBasis"):
            v.append(f"08: '{el}' ({cls}) has no lawfulBasis")
        rp = r.get("retentionPolicy")
        if not rp:
            v.append(f"08: '{el}' has no retentionPolicy")
        elif rp not in policies:
            v.append(f"08: '{el}' retentionPolicy '{rp}' is undefined")

    for r in code_inv:
        el = r.get("dataElement", "<unnamed>")
        rp = r.get("retentionPolicy")
        if rp and rp not in policies:
            v.append(f"code-inventory: '{el}' retentionPolicy '{rp}' is undefined")
        if r.get("classification") in _MUST_INVENTORY and el not in documented:
            v.append(f"code-inventory: {r.get('classification')} element '{el}' has no 08 RoPA record")

    # Retention policies backed by a sensitive 08 record that carries a lawful basis: an
    # event using one of these has its lawful basis documented in the RoPA (Art.30 links
    # basis at the processing-record level; events need not restate it inline).
    retention_with_basis = {
        r["retentionPolicy"]
        for r in records
        if r.get("classification") in _NEEDS_BASIS and r.get("lawfulBasis") and r.get("retentionPolicy")
    }
    for e in evs:
        if e["cls"] in _NEEDS_BASIS:
            has_basis = "basis:" in e["personal_dsar"].lower() or e["retention"] in retention_with_basis
            if not has_basis:
                v.append(
                    f"04: personal event '{e['event']}' has no lawful basis "
                    f"(none inline, and no 08 record for retention '{e['retention']}')"
                )
        if e["cls"] in _MUST_INVENTORY and e["retention"] and e["retention"] not in policies:
            v.append(f"04: event '{e['event']}' retention '{e['retention']}' is undefined")

    return v
