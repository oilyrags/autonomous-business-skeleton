"""Issue and validate short-lived agent JWTs (interim issuer, ADR-0003).

HS256 with a shared secret. Self-contained validation (no network call) so the
gateway can verify locally; revocation (slice 03) layers a state check on top.
"""

from datetime import UTC, datetime, timedelta

import jwt

from ab_common.config import settings


class InvalidToken(Exception):
    """Raised when a token is missing, malformed, expired, or mis-signed."""


def issue_token(agent_id: str, ttl_seconds: int = 300) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": agent_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def validate_token(token: str) -> str:
    """Return the agent id (``sub``) for a valid token, else raise InvalidToken."""
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except jwt.PyJWTError as exc:
        raise InvalidToken(str(exc)) from exc
    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise InvalidToken("token missing subject")
    return sub
