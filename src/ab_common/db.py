"""Postgres access + idempotent schema bootstrap for the walking skeleton."""

import time

import psycopg

from .config import settings

_DDL = [
    """
    CREATE TABLE IF NOT EXISTS decisions (
        decision_id      text PRIMARY KEY,
        title            text NOT NULL,
        agent_id         text NOT NULL,
        authority_level  int  NOT NULL,
        approval_status  text NOT NULL,
        business_id      text,
        created_at       timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_log (
        seq          bigserial PRIMARY KEY,
        occurred_at  timestamptz NOT NULL,
        principal    text NOT NULL,
        action       text NOT NULL,
        resource     text NOT NULL,
        outcome      text NOT NULL,
        payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
        prev_hash    text NOT NULL,
        hash         text NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS revoked_principals (
        principal    text PRIMARY KEY,
        revoked_at   timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS kill_switch (
        id            bigserial PRIMARY KEY,
        scope         text NOT NULL,
        target_id     text,
        active        boolean NOT NULL DEFAULT true,
        reason        text NOT NULL,
        activated_by  text NOT NULL,
        activated_at  timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS outbox (
        notification_id  text PRIMARY KEY,
        principal        text NOT NULL,
        recipient        text NOT NULL,
        body             text NOT NULL,
        created_at       timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ledger_txns (
        txn_id           text PRIMARY KEY,
        idempotency_key  text NOT NULL UNIQUE,
        maker            text NOT NULL,
        checker          text,
        magnitude        bigint NOT NULL,
        currency         text NOT NULL,
        memo             text NOT NULL DEFAULT '',
        business_id      text,
        created_at       timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ledger_entries (
        seq        bigserial PRIMARY KEY,
        txn_id     text NOT NULL REFERENCES ledger_txns(txn_id),
        account    text NOT NULL,
        amount     bigint NOT NULL,
        currency   text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS businesses (
        business_id   text PRIMARY KEY,
        name          text NOT NULL,
        status        text NOT NULL,
        capital_minor bigint NOT NULL,
        blueprint     jsonb NOT NULL,
        created_at    timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS experiments (
        experiment_id   text PRIMARY KEY,
        business_id     text NOT NULL,
        hypothesis      text NOT NULL,
        arms            jsonb NOT NULL,
        budget_minor    bigint NOT NULL,
        success_metrics jsonb NOT NULL,
        status          text NOT NULL DEFAULT 'proposed',
        decision        text,
        created_by      text NOT NULL,
        created_at      timestamptz NOT NULL DEFAULT now()
    )
    """,
]


def connect() -> psycopg.Connection:
    return psycopg.connect(settings.pg_dsn)


def init_db(retries: int = 15, delay: float = 2.0) -> None:
    """Create tables (idempotent), retrying the initial connect so startup tolerates
    the DB (or its mTLS sidecar) not being ready yet."""
    for attempt in range(retries):
        try:
            with connect() as conn:
                for stmt in _DDL:
                    conn.execute(stmt)
                conn.commit()
            return
        except psycopg.OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
