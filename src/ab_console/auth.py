"""Console authentication + CSRF defense (VULN-001).

The console mutates governed state — it can halt the whole fleet and approve high-stakes decisions —
so **no route is anonymous** and every mutation is bound to a real, non-spoofable operator identity.

Identity model: a trusted reverse proxy authenticates the human operator (e.g. via the existing
Keycloak OIDC) and forwards a **signed** identity on every request — `X-Operator-Id`,
`X-Operator-Role`, and `X-Operator-Sig = HMAC-SHA256(secret, "id:role")`. The console verifies the
signature with a shared secret, so a caller who reaches the console directly (bypassing the proxy)
cannot forge an operator without the secret. Default-deny: a missing or bad signature is a 401.

Because the signature is a *custom* header only the proxy can produce, a victim's browser cannot be
made to attach it on a cross-site request — that defeats CSRF at the auth layer. `check_origin`
adds a second, independent barrier (reject a cross-origin `Origin`) as defense in depth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, Request

from ab_common import operator_identity
from ab_common.config import settings
from ab_common.operator_identity import MUTATING_ROLES


@dataclass(frozen=True)
class Operator:
    """An authenticated console operator (identity asserted by the trusted proxy, signature-verified)."""

    id: str
    role: str

    @property
    def can_mutate(self) -> bool:
        return self.role in MUTATING_ROLES


def sign_identity(operator_id: str, role: str) -> str:
    """The signature the proxy must attach (exposed so tests + the proxy agree on one definition)."""
    return operator_identity.sign(operator_id, role, settings.operator_auth_secret)


def require_operator(
    x_operator_id: Annotated[str | None, Header()] = None,
    x_operator_role: Annotated[str | None, Header()] = None,
    x_operator_sig: Annotated[str | None, Header()] = None,
) -> Operator:
    """Resolve the authenticated operator from the signed proxy headers, or 401. Every route depends
    on this — there is no anonymous access."""
    if not (x_operator_id and x_operator_role):
        raise HTTPException(status_code=401, detail="operator authentication required")
    if not operator_identity.verify(
        x_operator_id, x_operator_role, x_operator_sig, settings.operator_auth_secret
    ):
        raise HTTPException(status_code=401, detail="invalid operator signature")
    return Operator(id=x_operator_id, role=x_operator_role)


def require_mutator(operator: Operator) -> Operator:
    """Guard a state-changing action: the operator must hold a mutating role (else 403)."""
    if not operator.can_mutate:
        raise HTTPException(status_code=403, detail=f"role '{operator.role}' may not perform this action")
    return operator


def check_origin(request: Request) -> None:
    """CSRF defense in depth: reject a cross-origin write. A same-origin browser form and
    server-to-server calls (no Origin) pass; a forged cross-site POST is refused."""
    origin = request.headers.get("origin")
    if origin is None:
        return
    host = request.headers.get("host", "")
    if origin.split("://", 1)[-1] != host:
        raise HTTPException(status_code=403, detail="cross-origin request refused")
