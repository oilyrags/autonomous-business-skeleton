"""OPA authorization client. Default-deny: any error or non-true result denies."""

import httpx

from ab_common.config import settings


class OpaUnavailable(Exception):
    """OPA could not be reached or errored — the gateway must fail closed with an audited deny."""


def authorize(
    principal: str, action: str, resource: str, purpose: str, business_id: str | None = None
) -> bool:
    # business_id is part of the policy input (VULN-002) so the rego policy — not just the code —
    # can bind an agent to the tenants it may act for.
    body = {
        "input": {
            "principal": principal,
            "action": action,
            "resource": resource,
            "purpose": purpose,
            "business_id": business_id,
        }
    }
    # An OPA outage must fail closed as an *audited* deny (VULN-007), not an unhandled 500: raise a
    # typed error the gateway maps to a 503 deny recorded in the audit log.
    try:
        resp = httpx.post(f"{settings.opa_url}/v1/data/ab/authz/allow", json=body, timeout=5.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise OpaUnavailable(str(exc)) from exc
    return resp.json().get("result") is True
