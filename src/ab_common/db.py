"""Postgres access + idempotent schema bootstrap for the walking skeleton."""

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
]


def connect() -> psycopg.Connection:
    return psycopg.connect(settings.pg_dsn)


def init_db() -> None:
    with connect() as conn:
        for stmt in _DDL:
            conn.execute(stmt)
        conn.commit()
