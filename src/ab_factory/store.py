"""Persisted Business Factory: the real provision flow (Postgres + ledger + bus).

Mirrors the `ab_ledger` core/store split — `core` holds the decisions, this wires the real
signals and persistence. Capital is booked as a double-entry ledger transaction; a business
that passes the readiness gate is activated and publishes `BusinessActivated`.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ab_common import bus, db
from ab_common.config import settings
from ab_compliance.ropa import check as ropa_check
from ab_factory import core
from ab_factory.core import Business, Status
from ab_growth.blueprint import Blueprint
from ab_killswitch import state as killswitch
from ab_ledger import store as ledger
from ab_ledger.core import Posting, Transaction

# Governed capital allocation is a maker-checker transaction (portfolio agent + treasury control).
_MAKER = "executive.portfolio_agent"
_CHECKER = "treasury.control_agent"


class AlreadyProvisioned(Exception):
    """A business with this business_id already exists."""


def _cash_account(business_id: str) -> str:
    return f"{business_id}:cash"


def _row_to_business(row: dict[str, Any]) -> Business:
    bp = Blueprint.model_validate(row["blueprint"])  # jsonb comes back as a dict
    return Business(blueprint=bp, capital_minor=int(row["capital_minor"]), status=Status(str(row["status"])))


def provision(blueprint: Blueprint, capital_minor: int) -> Business:
    """Full flow: reject-underfunded → persist draft → allocate capital → readiness → activate."""
    business = core.provision(blueprint, capital_minor)  # raises Underfunded (nothing written)

    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO businesses (business_id, name, status, capital_minor, blueprint) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (business_id) DO NOTHING RETURNING business_id",
            (business.business_id, business.name, Status.DRAFT, capital_minor, blueprint.model_dump_json()),
        )
        if cur.fetchone() is None:
            conn.rollback()
            raise AlreadyProvisioned(business.business_id)
        conn.commit()

    # Allocate capital: debit <business_id>:cash / credit portfolio:treasury (double-entry).
    ledger.post(
        Transaction(
            txn_id=f"cap_{uuid4().hex[:12]}",
            idempotency_key=f"capital-{business.business_id}",
            postings=(
                Posting(_cash_account(business.business_id), capital_minor),
                Posting("portfolio:treasury", -capital_minor),
            ),
            maker=_MAKER,
            checker=_CHECKER,
            memo=f"initial capital for {business.business_id}",
        )
    )

    readiness = core.readiness(
        business,
        cash_balance=ledger.account_balance(_cash_account(business.business_id)),
        kill_switch_clear=not killswitch.is_killed(business.business_id),
        compliance_clear=not ropa_check(),
    )
    core.activate(business, readiness)

    if business.status is Status.ACTIVE:
        _set_status(business.business_id, Status.ACTIVE)
        event = core.to_event(business)
        bus.publish_event(settings.business_topic, key=business.business_id, event=event)
    return business


def _set_status(business_id: str, status: Status) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE businesses SET status = %s WHERE business_id = %s", (status, business_id))
        conn.commit()


def get(business_id: str) -> Business | None:
    with db.connect() as conn:
        cur = conn.execute(
            "SELECT name, status, capital_minor, blueprint FROM businesses WHERE business_id = %s",
            (business_id,),
        )
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
    if row is None:
        return None
    return _row_to_business(dict(zip(cols, row, strict=True)))
