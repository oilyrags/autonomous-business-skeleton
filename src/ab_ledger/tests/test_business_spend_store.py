"""store.business_spend derives per-business spend from Postgres. Runs against `make up-infra`."""

import socket
import uuid
from collections.abc import Iterator

import pytest

from ab_common import db
from ab_ledger import store
from ab_ledger.core import LedgerSpend, Posting, Transaction


def _reachable(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture
def pg() -> Iterator[None]:
    if not _reachable("localhost", 55432):
        pytest.skip("Postgres not reachable — run `make up-infra` (PG 55432)")
    db.init_db()
    with db.connect() as conn:
        conn.execute("TRUNCATE ledger_entries, ledger_txns")
        conn.commit()
    yield


def _post(txn: Transaction) -> None:
    assert store.post(txn) is True


def test_business_spend_splits_llm_and_external_from_postgres(pg: None) -> None:
    bid = f"acme{uuid.uuid4().hex[:6]}"
    # LLM metering: debit {bid}:llm_spend, credit {bid}:cash.
    _post(
        Transaction(
            txn_id=f"m{uuid.uuid4().hex[:8]}",
            idempotency_key=f"m{uuid.uuid4().hex[:8]}",
            postings=(Posting(f"{bid}:llm_spend", 15_000), Posting(f"{bid}:cash", -15_000)),
            maker="gateway",
            business_id=bid,
        )
    )
    # Business-scoped external payment (unlisted payee → checker approves).
    _post(
        Transaction(
            txn_id=f"p{uuid.uuid4().hex[:8]}",
            idempotency_key=f"p{uuid.uuid4().hex[:8]}",
            postings=(Posting("external:ads_co", 40_000), Posting(f"{bid}:cash", -40_000)),
            maker="agent",
            checker="controller",
            business_id=bid,
            payee="ads_co",
        )
    )

    assert store.business_spend(bid) == LedgerSpend(bid, llm_spend_minor=15_000, external_spend_minor=40_000)


def test_business_with_no_activity_has_zero_spend(pg: None) -> None:
    assert store.business_spend("ghost") == LedgerSpend("ghost", 0, 0)
