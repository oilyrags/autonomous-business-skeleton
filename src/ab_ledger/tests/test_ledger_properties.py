"""Property-based tests for the ledger's money-critical invariants (pure, infra-free).

The double-entry ledger's whole point is that money is conserved. These check the invariants
hold for *arbitrary* sequences of balanced transactions, not just the hand-picked examples in
the unit tests: the trial balance is always zero, account balances sum to zero, and a replayed
idempotency key never moves money twice.
"""

from __future__ import annotations

from hypothesis import assume, given
from hypothesis import strategies as st

from ab_ledger.core import PAYMENT_CAP_MINOR, InMemoryLedger, Posting, Transaction

# Internal accounts only (no ``external:`` prefix) and magnitudes at/under the cap, so every
# generated transfer is auto-approvable — we are exercising the *balance* invariant, not the
# approval rules (those have their own tests).
_ACCOUNTS = st.sampled_from(["a:cash", "b:cash", "c:treasury", "d:ops", "e:reserve"])
_AMOUNT = st.integers(min_value=1, max_value=PAYMENT_CAP_MINOR)
# A balanced transfer = (debit account, credit account, amount).
_TRANSFER = st.tuples(_ACCOUNTS, _ACCOUNTS, _AMOUNT)


def _post_transfers(ledger: InMemoryLedger, transfers: list[tuple[str, str, int]]) -> None:
    for i, (debit, credit, amount) in enumerate(transfers):
        txn = Transaction(
            txn_id=f"t{i}",
            idempotency_key=f"k{i}",
            postings=(Posting(debit, amount), Posting(credit, -amount)),
            maker="maker",
        )
        ledger.post(txn)


@given(st.lists(_TRANSFER, max_size=30))
def test_trial_balance_is_always_zero(transfers: list[tuple[str, str, int]]) -> None:
    ledger = InMemoryLedger()
    _post_transfers(ledger, transfers)
    assert ledger.trial_balance() == 0


@given(st.lists(_TRANSFER, max_size=30))
def test_account_balances_sum_to_zero(transfers: list[tuple[str, str, int]]) -> None:
    ledger = InMemoryLedger()
    _post_transfers(ledger, transfers)
    accounts = ["a:cash", "b:cash", "c:treasury", "d:ops", "e:reserve"]
    assert sum(ledger.account_balance(a) for a in accounts) == 0


@given(debit=_ACCOUNTS, credit=_ACCOUNTS, amount=_AMOUNT, replays=st.integers(1, 6))
def test_replaying_an_idempotency_key_moves_money_once(
    debit: str, credit: str, amount: int, replays: int
) -> None:
    assume(debit != credit)  # distinct accounts so the debit's balance is unambiguous
    ledger = InMemoryLedger()
    txn = Transaction(
        txn_id="t",
        idempotency_key="k",
        postings=(Posting(debit, amount), Posting(credit, -amount)),
        maker="maker",
    )
    outcomes = [ledger.post(txn) for _ in range(replays)]
    assert outcomes[0] is True  # first application posts
    assert all(o is False for o in outcomes[1:])  # every replay is a no-op
    assert ledger.account_balance(debit) == amount  # applied exactly once, not `replays` times
    assert ledger.trial_balance() == 0
