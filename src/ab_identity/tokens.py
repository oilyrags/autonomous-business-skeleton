"""Validate agent tokens issued by Keycloak (OIDC, RS256) — see ADR-0004.

The gateway verifies the token signature against Keycloak's JWKS and reads the
``azp`` claim (the client_id) as the principal. Issuer/audience are not verified
in the skeleton (documented simplification in ADR-0004).
"""

import jwt
from jwt import PyJWKClient

from ab_common.config import settings


class InvalidToken(Exception):
    """Raised when a token is missing, malformed, expired, or mis-signed."""


# Cached across calls; fetches/refreshes JWKS lazily on first use.
_jwk_client = PyJWKClient(settings.oidc_jwks_url)


def validate_token(token: str) -> str:
    """Return the agent id (``azp``) for a valid token, else raise InvalidToken."""
    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_iss": False},
        )
    except Exception as exc:  # jwt errors or JWKS fetch failures
        raise InvalidToken(str(exc)) from exc

    azp = claims.get("azp") or claims.get("client_id")
    if not isinstance(azp, str):
        raise InvalidToken("token missing azp/client_id claim")
    return azp
