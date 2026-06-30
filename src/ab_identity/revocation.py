"""Principal revocation — the source of truth the gateway checks each call.

Lives in identity (outside the gateway) per ADR-0003: the gateway trusts an
external store, so a revoked agent is cut off independent of token expiry.
"""

from ab_common import db


def revoke(principal: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO revoked_principals (principal) VALUES (%s) ON CONFLICT DO NOTHING",
            (principal,),
        )
        conn.commit()


def is_revoked(principal: str) -> bool:
    with db.connect() as conn:
        row = conn.execute("SELECT 1 FROM revoked_principals WHERE principal=%s", (principal,)).fetchone()
    return row is not None
