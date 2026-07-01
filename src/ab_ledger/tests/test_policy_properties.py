"""Property-based tests for the ledger's money-authority policy (pure, infra-free).

The approval policy is money-critical: any payment over the cap OR to a payee not on the allow-list
must be approved by a *distinct* checker (maker-checker + separation of duties). These assert that
enforcement for arbitrary payments, not just the hand-picked unit cases.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ab_ledger.core import (
    ApprovalRequired,
    Posting,
    SeparationOfDutiesViolation,
    Transaction,
    requires_approval,
    validate,
)

_CAP = 100_000
_APPROVED = frozenset({"acme"})  # only this payee is pre-approved
_MAKER = "maker"

# An outbound payment: to a payee (approved or not), for an amount (under/over the cap), with no
# checker / the maker as checker / a distinct checker.
_PAYEE = st.sampled_from(["acme", "globex", "initech"])
_AMOUNT = st.integers(min_value=1, max_value=300_000)
_CHECKER = st.sampled_from([None, _MAKER, "controller"])


def _payment(payee: str, amount: int, checker: str | None) -> Transaction:
    return Transaction(
        txn_id="t",
        idempotency_key="k",
        postings=(Posting(f"external:{payee}", amount), Posting("cash", -amount)),
        maker=_MAKER,
        checker=checker,
        payee=payee,
    )


@given(payee=_PAYEE, amount=_AMOUNT, checker=_CHECKER)
def test_over_cap_or_new_payee_needs_a_distinct_checker(payee: str, amount: int, checker: str | None) -> None:
    txn = _payment(payee, amount, checker)
    if not requires_approval(txn, _CAP, _APPROVED):
        validate(txn, _CAP, _APPROVED)  # within cap + approved payee → posts, checker irrelevant
        return
    if checker is None:
        with pytest.raises(ApprovalRequired):
            validate(txn, _CAP, _APPROVED)
    elif checker == _MAKER:
        with pytest.raises(SeparationOfDutiesViolation):  # separation of duties
            validate(txn, _CAP, _APPROVED)
    else:
        validate(txn, _CAP, _APPROVED)  # a distinct checker approves it


@given(amount=st.integers(min_value=1, max_value=_CAP), checker=_CHECKER)
def test_approved_payee_under_cap_never_needs_approval(amount: int, checker: str | None) -> None:
    txn = _payment("acme", amount, checker)  # approved payee, at/under the cap
    assert requires_approval(txn, _CAP, _APPROVED) is False
    validate(txn, _CAP, _APPROVED)  # always posts, with or without a checker


@given(amount=st.integers(min_value=_CAP + 1, max_value=1_000_000))
def test_over_cap_is_always_gated_even_for_an_approved_payee(amount: int) -> None:
    txn = _payment("acme", amount, checker=None)  # approved payee but over the cap
    assert requires_approval(txn, _CAP, _APPROVED) is True
    with pytest.raises(ApprovalRequired):
        validate(txn, _CAP, _APPROVED)
