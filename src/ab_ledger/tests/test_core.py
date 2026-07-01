"""Infra-free: the ledger's balance invariant, double-payment prevention, maker-checker+SoD."""

import pytest

from ab_ledger.core import (
    ApprovalRequired,
    InMemoryLedger,
    Posting,
    SeparationOfDutiesViolation,
    Transaction,
    UnbalancedTransaction,
    is_balanced,
    requires_approval,
    validate,
)


def _txn(tid: str, key: str, postings: list[Posting], maker: str = "cfo_agent", checker: str | None = None):
    return Transaction(tid, key, tuple(postings), maker=maker, checker=checker)


def test_balanced_transaction_is_valid() -> None:
    t = _txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -50_000)])
    assert is_balanced(t)
    validate(t)  # does not raise


def test_unbalanced_transaction_is_rejected() -> None:
    t = _txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -49_999)])
    assert not is_balanced(t)
    with pytest.raises(UnbalancedTransaction):
        validate(t)


def test_empty_transaction_is_rejected() -> None:
    with pytest.raises(UnbalancedTransaction):
        validate(_txn("t1", "k1", []))


def test_ledger_balance_invariant_holds() -> None:
    led = InMemoryLedger()
    led.post(_txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -50_000)]))
    led.post(_txn("t2", "k2", [Posting("expense", 30_000), Posting("cash", -30_000)]))
    assert led.trial_balance() == 0  # the invariant
    assert led.account_balance("cash") == 20_000
    assert led.account_balance("revenue") == -50_000


def test_double_payment_is_prevented() -> None:
    led = InMemoryLedger()
    t = _txn("t1", "k1", [Posting("cash", 50_000), Posting("revenue", -50_000)])
    assert led.post(t) is True
    assert led.post(t) is False  # same idempotency key -> no-op
    assert led.account_balance("cash") == 50_000  # applied exactly once
    assert led.trial_balance() == 0


def test_over_cap_payment_requires_a_checker() -> None:
    big = [Posting("vendor", 150_000), Posting("cash", -150_000)]
    assert requires_approval(_txn("p1", "kp1", big))
    with pytest.raises(ApprovalRequired):
        validate(_txn("p1", "kp1", big))  # no checker


def test_checker_must_differ_from_maker() -> None:
    big = [Posting("vendor", 150_000), Posting("cash", -150_000)]
    with pytest.raises(SeparationOfDutiesViolation):
        validate(_txn("p2", "kp2", big, maker="cfo_agent", checker="cfo_agent"))


def test_over_cap_payment_with_distinct_checker_is_valid() -> None:
    big = [Posting("vendor", 150_000), Posting("cash", -150_000)]
    led = InMemoryLedger()
    assert led.post(_txn("p3", "kp3", big, maker="cfo_agent", checker="controller_agent")) is True
    assert led.trial_balance() == 0


def test_under_cap_payment_needs_no_checker() -> None:
    small = [Posting("vendor", 50_000), Posting("cash", -50_000)]
    validate(_txn("s1", "ks1", small))  # magnitude below cap -> no approval needed


def test_new_payee_under_cap_requires_a_checker() -> None:
    # AM-11: a payment to a payee not on the approved list needs maker-checker, even under cap.
    small = [Posting("payout", 50_000), Posting("cash", -50_000)]
    t = Transaction("np1", "knp1", tuple(small), maker="cfo_agent", payee="brand_new_vendor")
    with pytest.raises(ApprovalRequired):
        validate(t, approved_payees=frozenset())


def test_approved_payee_under_cap_needs_no_checker() -> None:
    small = [Posting("payout", 50_000), Posting("cash", -50_000)]
    t = Transaction("np2", "knp2", tuple(small), maker="cfo_agent", payee="known_vendor")
    validate(t, approved_payees=frozenset({"known_vendor"}))  # on the list -> no approval


def test_new_payee_with_distinct_checker_is_valid() -> None:
    small = [Posting("payout", 50_000), Posting("cash", -50_000)]
    t = Transaction(
        "np3", "knp3", tuple(small), maker="cfo_agent", checker="controller_agent", payee="new_vendor"
    )
    validate(t, approved_payees=frozenset())  # approved by a distinct checker
