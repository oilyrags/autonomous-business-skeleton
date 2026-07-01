"""Ledger invariants self-check (deterministic, no infra).

    uv run python -m ab_ledger

Proves the three Audit-7 controls hold: the balance invariant (a ledger of balanced
transactions sums to 0), double-payment prevention (a replayed idempotency key posts
nothing), and maker-checker + separation-of-duties for payments above the cap. Exits
non-zero if any invariant fails.
"""

from __future__ import annotations

import sys

from ab_ledger.core import (
    PAYMENT_CAP_MINOR,
    ApprovalRequired,
    InMemoryLedger,
    Posting,
    SeparationOfDutiesViolation,
    Transaction,
    UnbalancedTransaction,
)


def _txn(tid: str, key: str, postings: list[Posting], maker: str, checker: str | None = None) -> Transaction:
    return Transaction(
        txn_id=tid, idempotency_key=key, postings=tuple(postings), maker=maker, checker=checker
    )


def _raises(exc: type[Exception], fn: object, label: str) -> bool:
    try:
        fn()  # type: ignore[operator]
        print(f"  [FAIL] {label}: expected {exc.__name__}, none raised")
        return False
    except exc:
        print(f"  [ok] {label}: {exc.__name__} raised")
        return True


def main() -> int:
    ok = True
    ledger = InMemoryLedger()

    print("== balance invariant ==")
    ledger.post(_txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -50_000)], "cfo_agent"))
    ledger.post(_txn("t2", "k2", [Posting("expense", 30_000), Posting("cash", -30_000)], "cfo_agent"))
    tb = ledger.trial_balance()
    print(f"  trial_balance = {tb} (must be 0); cash = {ledger.account_balance('cash')}")
    ok = ok and tb == 0
    ok = ok and _raises(
        UnbalancedTransaction,
        lambda: ledger.post(_txn("bad", "kbad", [Posting("cash", 10), Posting("revenue", -9)], "cfo_agent")),
        "unbalanced rejected",
    )

    print("== double-payment prevention ==")
    dup = _txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -50_000)], "cfo_agent")
    applied = ledger.post(dup)  # same idempotency key as t1
    print(f"  replay applied? {applied} (must be False); trial_balance still {ledger.trial_balance()}")
    ok = ok and applied is False and ledger.trial_balance() == 0

    print(f"== maker-checker + SoD (cap {PAYMENT_CAP_MINOR}) ==")
    big = [Posting("vendor", 150_000), Posting("cash", -150_000)]
    ok = ok and _raises(
        ApprovalRequired, lambda: ledger.post(_txn("p1", "kp1", big, "cfo_agent")), "over-cap needs checker"
    )
    ok = ok and _raises(
        SeparationOfDutiesViolation,
        lambda: ledger.post(_txn("p2", "kp2", big, "cfo_agent", checker="cfo_agent")),
        "checker must differ from maker",
    )
    approved = ledger.post(_txn("p3", "kp3", big, "cfo_agent", checker="controller_agent"))
    print(f"  approved over-cap payment applied? {approved} (must be True)")
    ok = ok and approved is True and ledger.trial_balance() == 0

    print("ledger invariants: PASS" if ok else "ledger invariants: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
