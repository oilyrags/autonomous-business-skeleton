"""Append-only, idempotent ledger persistence (Postgres). Mirrors core.InMemoryLedger.

Idempotency is enforced at the database: the transaction header's ``idempotency_key`` is
UNIQUE and inserted ``ON CONFLICT DO NOTHING`` — a replayed payment lands zero rows and posts
nothing (double-payment prevented atomically). Validation runs before any write, so an
unbalanced or unapproved transaction never touches the ledger.
"""

from __future__ import annotations

from ab_common import db
from ab_ledger.core import PAYMENT_CAP_MINOR, Transaction, validate


def post(txn: Transaction, cap: int = PAYMENT_CAP_MINOR) -> bool:
    """Validate then persist atomically. Returns True if applied, False if a duplicate."""
    validate(txn, cap)  # raises on a rule violation before any DB write
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO ledger_txns (txn_id, idempotency_key, maker, checker, magnitude, currency, memo) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (idempotency_key) DO NOTHING RETURNING txn_id",
            (txn.txn_id, txn.idempotency_key, txn.maker, txn.checker, txn.magnitude, txn.currency, txn.memo),
        )
        if cur.fetchone() is None:
            conn.rollback()  # duplicate idempotency_key — nothing posted
            return False
        for p in txn.postings:
            conn.execute(
                "INSERT INTO ledger_entries (txn_id, account, amount, currency) VALUES (%s, %s, %s, %s)",
                (txn.txn_id, p.account, p.amount, txn.currency),
            )
        conn.commit()
    return True


def trial_balance() -> int:
    """The balance invariant — always 0 for a ledger of balanced transactions."""
    with db.connect() as conn:
        row = conn.execute("SELECT coalesce(sum(amount), 0) FROM ledger_entries").fetchone()
    return int(row[0]) if row else 0


def account_balance(account: str) -> int:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT coalesce(sum(amount), 0) FROM ledger_entries WHERE account = %s", (account,)
        ).fetchone()
    return int(row[0]) if row else 0
