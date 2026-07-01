"""Deterministic double-entry ledger primitives (no I/O, no floats).

Money is **integer minor units** (e.g. cents) — never a float — so arithmetic is exact and
reproducible. A transaction is a set of signed postings (+ debit, − credit) that MUST sum to
zero; the whole ledger therefore always sums to zero (the balance invariant). Payments above
the cap require a *checker* distinct from the *maker* (maker-checker + separation of duties).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# Payments whose magnitude exceeds this (in minor units) require maker-checker approval.
PAYMENT_CAP_MINOR: int = int(os.environ.get("AB_PAYMENT_CAP_MINOR", "100000"))  # e.g. 1000.00
# Known/approved payees. A payment to a payee NOT on this list requires approval too
# (AM-11: new payee → maker-checker), even under the cap. Env is a comma-separated list.
APPROVED_PAYEES: frozenset[str] = frozenset(filter(None, os.environ.get("AB_APPROVED_PAYEES", "").split(",")))


class LedgerError(Exception):
    """Base for all ledger rule violations."""


class UnbalancedTransaction(LedgerError):
    """Debits and credits do not sum to zero."""


class ApprovalRequired(LedgerError):
    """A payment above the cap (or to a new payee) has no checker."""


class SeparationOfDutiesViolation(LedgerError):
    """The checker is the same principal as the maker."""


@dataclass(frozen=True)
class Posting:
    account: str
    amount: int  # signed minor units: + debit, − credit


@dataclass(frozen=True)
class Transaction:
    txn_id: str
    idempotency_key: str
    postings: tuple[Posting, ...]
    maker: str
    checker: str | None = None
    currency: str = "EUR"
    memo: str = ""
    payee: str | None = None  # external counterparty for a payment (None = internal transfer)

    @property
    def magnitude(self) -> int:
        """The money moved = total debits (== total credits for a balanced txn)."""
        return sum(p.amount for p in self.postings if p.amount > 0)


def is_balanced(txn: Transaction) -> bool:
    return bool(txn.postings) and sum(p.amount for p in txn.postings) == 0


def approval_reason(
    txn: Transaction, cap: int = PAYMENT_CAP_MINOR, approved_payees: frozenset[str] = APPROVED_PAYEES
) -> str | None:
    """Why this txn needs maker-checker, or None if it doesn't. Deterministic."""
    if txn.magnitude > cap:
        return f"payment {txn.magnitude} > cap {cap}"
    if txn.payee is not None and txn.payee not in approved_payees:
        return f"new payee '{txn.payee}' not on the approved list"
    return None


def requires_approval(
    txn: Transaction, cap: int = PAYMENT_CAP_MINOR, approved_payees: frozenset[str] = APPROVED_PAYEES
) -> bool:
    return approval_reason(txn, cap, approved_payees) is not None


def validate(
    txn: Transaction, cap: int = PAYMENT_CAP_MINOR, approved_payees: frozenset[str] = APPROVED_PAYEES
) -> None:
    """Raise if the transaction breaks a ledger rule. Deterministic; no side effects."""
    if not txn.postings:
        raise UnbalancedTransaction(f"{txn.txn_id}: no postings")
    if not is_balanced(txn):
        total = sum(p.amount for p in txn.postings)
        raise UnbalancedTransaction(f"{txn.txn_id}: postings sum to {total}, not 0")
    reason = approval_reason(txn, cap, approved_payees)
    if reason is not None:
        if txn.checker is None:
            raise ApprovalRequired(f"{txn.txn_id}: {reason} — needs a checker")
        if txn.checker == txn.maker:
            raise SeparationOfDutiesViolation(f"{txn.txn_id}: checker must differ from maker {txn.maker}")


@dataclass
class InMemoryLedger:
    """Append-only, idempotent ledger for tests + the demo. The Postgres store mirrors this."""

    _entries: list[Posting] = field(default_factory=list)
    _keys: set[str] = field(default_factory=set)

    def post(
        self,
        txn: Transaction,
        cap: int = PAYMENT_CAP_MINOR,
        approved_payees: frozenset[str] = APPROVED_PAYEES,
    ) -> bool:
        """Validate then apply. Returns True if applied, False if a duplicate (idempotent)."""
        validate(txn, cap, approved_payees)  # raises on any rule violation BEFORE mutating state
        if txn.idempotency_key in self._keys:
            return False  # double-payment prevented
        self._keys.add(txn.idempotency_key)
        self._entries.extend(txn.postings)
        return True

    def trial_balance(self) -> int:
        """The balance invariant: this is always 0 for a ledger of balanced transactions."""
        return sum(p.amount for p in self._entries)

    def account_balance(self, account: str) -> int:
        return sum(p.amount for p in self._entries if p.account == account)
