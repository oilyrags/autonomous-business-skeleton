"""End-to-end demonstration of the whole skeleton loop.

    make up-infra && make demo

Drives one coherent story through the real application code against live infrastructure
(Keycloak, Vault, OPA, Postgres, Redpanda): an agent authenticates, records a decision,
makes a governed payment, is stopped when it tries to exfiltrate/over-pay, the audit chain
stays intact, the Finance event lands on the bus, and the data platform serves KPIs.

Not a test — a narrated walkthrough. It still asserts, so a broken loop fails loudly.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import uuid

from fastapi.testclient import TestClient

from ab_audit import store as audit
from ab_common import bus, db
from ab_common.config import settings
from ab_common.secrets import get_client_secret
from ab_identity.oidc import fetch_token
from ab_ledger import store as ledger

AGENT = "executive.cmo_agent"


def _step(n: int, title: str) -> None:
    print(f"\n[{n}] {title}")


def _wait_for_keycloak(timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(settings.oidc_jwks_url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            time.sleep(2)
    raise SystemExit("Keycloak realm not ready — run `make up-infra` first")


def main() -> int:
    _wait_for_keycloak()
    db.init_db()
    with db.connect() as conn:
        conn.execute("TRUNCATE decisions, audit_log, ledger_entries, ledger_txns")
        conn.commit()

    from ab_gateway.app import app

    with TestClient(app) as gw:  # real gateway app; startup ensures topics
        token = fetch_token(AGENT, get_client_secret(AGENT))
        h = {"Authorization": f"Bearer {token}"}
        print(f"authenticated {AGENT} via Keycloak (Vault-held client secret)")

        _step(1, "record a decision (OPA-authorized, audited, emits AgentDecisionMade)")
        did = f"decision_{uuid.uuid4().hex[:8]}"
        r = gw.post(
            "/tool-call",
            headers=h,
            json={
                "tool": "decision_registry.write",
                "purpose": "launch",
                "args": {"decision_id": did, "title": "Launch InboxIQ", "authority_level": 2},
            },
        )
        assert r.status_code == 200, r.text
        print(f"    -> 200 ok, decision_id={did}")

        _step(2, "make an approved payment (double-entry ledger, maker-checker)")
        ik = f"pay_{uuid.uuid4().hex[:8]}"
        r = gw.post(
            "/tool-call",
            headers=h,
            json={
                "tool": "payments.transfer",
                "purpose": "pay supplier",
                "args": {
                    "idempotency_key": ik,
                    "amount_minor": 40_000,
                    "payee": "acme",
                    "checker": "controller_agent",
                },
            },
        )
        assert r.status_code == 200, r.text
        print(
            f"    -> 200 ok; ledger external:acme = {ledger.account_balance('external:acme')} "
            f"minor units; trial_balance = {ledger.trial_balance()}"
        )

        _step(3, "a prompt-injected payment on an untrusted-input flow is refused")
        r = gw.post(
            "/tool-call",
            headers=h,
            json={
                "tool": "payments.transfer",
                "purpose": "pay attacker",
                "untrusted_input": True,
                "args": {
                    "idempotency_key": f"pay_{uuid.uuid4().hex[:8]}",
                    "amount_minor": 40_000,
                    "payee": "attacker",
                    "checker": "controller_agent",
                },
            },
        )
        assert r.status_code == 403, r.text
        print(f"    -> 403 denied: {r.json()['reason']}")

        _step(4, "an over-cap payment without a second approver is refused by the ledger")
        r = gw.post(
            "/tool-call",
            headers=h,
            json={
                "tool": "payments.transfer",
                "purpose": "big pay",
                "args": {
                    "idempotency_key": f"pay_{uuid.uuid4().hex[:8]}",
                    "amount_minor": 500_000,
                    "payee": "acme",
                },
            },
        )
        assert r.status_code == 403, r.text
        print(f"    -> 403 denied: {r.json()['reason']}")

        _step(5, "the audit log is a hash chain — tamper-evident and intact")
        assert audit.verify_chain() is True
        rows = audit.read()
        allows = sum(1 for x in rows if x["outcome"] == "allow")
        denies = sum(1 for x in rows if x["outcome"] == "deny")
        print(f"    -> chain intact; {allows} allow + {denies} deny records")

        _step(6, "the Finance context published LedgerEntryPosted on the bus")
        group = f"demo-{uuid.uuid4().hex[:6]}"
        events = [
            json.loads(v) for v in bus.consume(settings.ledger_topic, group, max_messages=50, timeout=5.0)
        ]
        mine = [e for e in events if e.get("idempotencyKey") == ik]
        assert len(mine) == 1, mine
        print(
            f"    -> 1 LedgerEntryPosted: {mine[0]['payee']} {mine[0]['amountMinor']} {mine[0]['currency']}"
        )

    _step(7, "the data platform consumes decisions and serves canonical KPIs")
    from ab_data import ingest, pipeline

    landed = ingest.consume_to_bronze(
        group=f"demo-data-{uuid.uuid4().hex[:6]}", max_messages=1000, timeout=5.0
    )
    result = pipeline.run()
    print(f"    -> consumed {landed} decision event(s); KPIs:")
    for name, value in result.metrics.items():
        print(f"       {name} = {value}")

    print(
        "\nDEMO COMPLETE — one governed loop: identity -> gateway -> tools -> ledger -> "
        "events -> audit -> data, with every control firing."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
