"""Guard against drift between the code-layer tenant grants (ab_gateway/authz.py) and the OPA policy
(config/opa/policy.rego): both enforce tenant binding, so a principal granted portfolio-wide access
in one must be granted it in the other (ADR-0057 follow-up). Infra-free — reads the files."""

from __future__ import annotations

from pathlib import Path

from ab_gateway import authz

_REGO = Path(__file__).resolve().parents[3] / "config" / "opa" / "policy.rego"


def test_wildcard_authz_grants_are_mirrored_in_the_opa_policy() -> None:
    rego = _REGO.read_text()
    for principal, grant in authz._GRANTS.items():
        if authz.WILDCARD in grant.businesses:
            assert f'"{principal}": ["*"]' in rego, (
                f"{principal} has a portfolio-wide (*) grant in authz.py but not in policy.rego — "
                "the two tenant-binding sources have drifted"
            )
