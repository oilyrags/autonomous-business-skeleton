"""Signed operator identity shared by the services that accept human interventions (VULN-001/004).

A trusted reverse proxy authenticates the human operator and forwards a signed identity —
`X-Operator-Id`, `X-Operator-Role`, and `X-Operator-Sig = HMAC-SHA256(secret, "id:role")`. Any
service that mutates governed state (the console, the kill-switch service) verifies the signature
with the shared secret, so a caller that reaches the service directly — an agent container on the
mesh, a request that bypassed the proxy — cannot forge an operator without the secret. One
definition, verified everywhere. Pure (no web framework), so it is unit-testable in isolation.
"""

from __future__ import annotations

import hmac
from hashlib import sha256

# Roles permitted to perform a state-changing intervention (halt, approve/reject). Read access only
# needs an authenticated operator; mutation needs one of these (least privilege).
MUTATING_ROLES = frozenset({"operator", "security", "admin"})


def sign(operator_id: str, role: str, secret: str) -> str:
    """The signature the trusted proxy must attach (shared so proxy + verifiers agree on one form)."""
    return hmac.new(secret.encode(), f"{operator_id}:{role}".encode(), sha256).hexdigest()


def verify(operator_id: str | None, role: str | None, sig: str | None, secret: str) -> bool:
    """True iff the identity is present and the signature is valid (constant-time, default-deny)."""
    if not (operator_id and role and sig):
        return False
    return hmac.compare_digest(sign(operator_id, role, secret), sig)
