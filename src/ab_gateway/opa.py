"""OPA authorization client. Default-deny: any error or non-true result denies."""

import httpx

from ab_common.config import settings


def authorize(principal: str, action: str, resource: str, purpose: str) -> bool:
    body = {"input": {"principal": principal, "action": action, "resource": resource, "purpose": purpose}}
    resp = httpx.post(f"{settings.opa_url}/v1/data/ab/authz/allow", json=body, timeout=5.0)
    resp.raise_for_status()
    return resp.json().get("result") is True
