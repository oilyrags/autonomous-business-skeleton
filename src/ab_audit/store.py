"""Append-only, hash-chained audit log (tamper-evident evidence backbone).

Each row's hash = HMAC-SHA256(key, prev_hash + canonical(row fields)) — the key lives outside the
DB (VULN-006), so a DB-write adversary cannot re-forge the chain: without the key they can't compute
a valid successor hash, and ``verify_chain`` (which uses the same key) detects the break. The first
row links the literal ``GENESIS``. Appends serialize on a transaction-scoped advisory lock so
concurrent writers can't fork the chain.
"""

import hmac
import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ab_common import db
from ab_common.config import settings

GENESIS = "GENESIS"
_APPEND_LOCK = 0x4A_44_49_54  # a fixed key for pg_advisory_xact_lock ("AUDIT") — serializes appends


def _canonical(
    occurred_at_iso: str, principal: str, action: str, resource: str, outcome: str, payload: dict[str, Any]
) -> str:
    return json.dumps(
        {
            "occurred_at": occurred_at_iso,
            "principal": principal,
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _hash(prev_hash: str, canonical: str) -> str:
    """Keyed chain link: HMAC-SHA256 under the audit key (held outside the DB, VULN-006)."""
    return hmac.new(settings.audit_hmac_key.encode(), (prev_hash + canonical).encode(), sha256).hexdigest()


def append(
    principal: str, action: str, resource: str, outcome: str, payload: dict[str, Any] | None = None
) -> str:
    """Append one immutable record; return its hash."""
    payload = payload or {}
    occurred_at = datetime.now(tz=UTC)
    occurred_at_iso = occurred_at.isoformat()
    with db.connect() as conn:
        # Serialize appenders (VULN-006): the transaction-scoped advisory lock makes read-tail +
        # insert atomic across connections, so two concurrent appends can't link the same prev_hash
        # and fork the chain. Released automatically on commit.
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (_APPEND_LOCK,))
        row = conn.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
        prev_hash = row[0] if row else GENESIS
        h = _hash(prev_hash, _canonical(occurred_at_iso, principal, action, resource, outcome, payload))
        conn.execute(
            "INSERT INTO audit_log (occurred_at, principal, action, resource, outcome, payload, "
            "prev_hash, hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (occurred_at, principal, action, resource, outcome, Jsonb(payload), prev_hash, h),
        )
        conn.commit()
    return h


def read(principal: str | None = None, action: str | None = None) -> list[dict[str, Any]]:
    clauses, params = [], []
    if principal is not None:
        clauses.append("principal = %s")
        params.append(principal)
    if action is not None:
        clauses.append("action = %s")
        params.append(action)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with db.connect() as conn:
        cur = conn.cursor(row_factory=dict_row)
        cur.execute(f"SELECT * FROM audit_log {where} ORDER BY seq", params)
        return list(cur.fetchall())


def verify_chain() -> bool:
    """Recompute the chain; return True iff every row's hash and link are intact."""
    with db.connect() as conn:
        cur = conn.cursor(row_factory=dict_row)
        cur.execute("SELECT * FROM audit_log ORDER BY seq")
        prev = GENESIS
        for r in cur.fetchall():
            occurred_at_iso = r["occurred_at"].astimezone(UTC).isoformat()
            expected = _hash(
                prev,
                _canonical(
                    occurred_at_iso, r["principal"], r["action"], r["resource"], r["outcome"], r["payload"]
                ),
            )
            if r["prev_hash"] != prev or r["hash"] != expected:
                return False
            prev = r["hash"]
    return True
