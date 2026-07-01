"""Persisted ledger: the invariant, double-payment injection, maker-checker — against Postgres."""

import pytest

from ab_ledger import store
from ab_ledger.core import ApprovalRequired, Posting, Transaction


def _txn(tid: str, key: str, postings: list[Posting], maker: str = "cfo_agent", checker: str | None = None):
    return Transaction(tid, key, tuple(postings), maker=maker, checker=checker)


def test_persisted_balance_invariant(pg: None) -> None:
    store.post(_txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -50_000)]))
    store.post(_txn("t2", "k2", [Posting("expense", 30_000), Posting("cash", -30_000)]))
    assert store.trial_balance() == 0  # the invariant holds in the DB
    assert store.account_balance("cash") == 20_000


def test_double_payment_injection_posts_nothing(pg: None) -> None:
    t = _txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -50_000)])
    assert store.post(t) is True
    # Replay the same idempotency key (a re-submitted payment) — must be a no-op.
    assert store.post(t) is False
    assert store.account_balance("cash") == 50_000  # not doubled
    assert store.trial_balance() == 0


def test_maker_checker_enforced_before_persistence(pg: None) -> None:
    big = [Posting("vendor", 150_000), Posting("cash", -150_000)]
    with pytest.raises(ApprovalRequired):
        store.post(_txn("p1", "kp1", big))  # over cap, no checker
    assert store.trial_balance() == 0  # nothing was written


def test_maker_checker_approved_payment_persists(pg: None) -> None:
    big = [Posting("vendor", 150_000), Posting("cash", -150_000)]
    assert store.post(_txn("p3", "kp3", big, maker="cfo_agent", checker="controller_agent")) is True
    assert store.account_balance("vendor") == 150_000
    assert store.trial_balance() == 0
