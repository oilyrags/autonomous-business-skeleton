"""Runtime configuration, read from the environment with local-dev defaults.

Non-secret defaults target the local docker-compose stack (ports published on localhost).
Secret-bearing settings (DB credentials, the Vault token, the operator-identity secret) are
**fail-closed outside dev** (VULN-005): a weak default is used only when ``AB_ENV`` is a dev
environment; in any other environment an unset secret raises at startup rather than silently
falling back to a known-weak value.
"""

import os

# Dev/test/local get convenience defaults; every other AB_ENV must supply secrets explicitly.
_DEV_ENVS = frozenset({"dev", "test", "local", "ci"})
_ENV = os.environ.get("AB_ENV", "dev")
_IS_DEV = _ENV in _DEV_ENVS


def _secret(var: str, dev_default: str) -> str:
    """A secret-bearing setting: the env value if set; a dev default only in a dev environment;
    otherwise refuse to start rather than run on a known-weak default (fail-closed)."""
    value = os.environ.get(var)
    if value:
        return value
    if _IS_DEV:
        return dev_default
    raise RuntimeError(
        f"{var} must be set when AB_ENV={_ENV!r} — refusing to fall back to an insecure default"
    )


class Settings:
    pg_dsn: str = _secret("AB_PG_DSN", "postgresql://ab:ab@localhost:55432/ab")  # carries DB credentials
    opa_url: str = os.environ.get("AB_OPA_URL", "http://localhost:8181")
    kafka_bootstrap: str = os.environ.get("AB_KAFKA", "localhost:19092")
    decision_topic: str = os.environ.get("AB_DECISION_TOPIC", "executive.decision.made")
    kill_topic: str = os.environ.get("AB_KILL_TOPIC", "security.killswitch.activated")
    ledger_topic: str = os.environ.get("AB_LEDGER_TOPIC", "finance.ledger.posted")
    business_topic: str = os.environ.get("AB_BUSINESS_TOPIC", "executive.business.activated")
    experiment_topic: str = os.environ.get("AB_EXPERIMENT_TOPIC", "growth.experiment.created")
    experiment_concluded_topic: str = os.environ.get(
        "AB_EXPERIMENT_CONCLUDED_TOPIC", "growth.experiment.concluded"
    )
    product_topic: str = os.environ.get("AB_PRODUCT_TOPIC", "product.initiative.scaffolded")
    product_stage_topic: str = os.environ.get("AB_PRODUCT_STAGE_TOPIC", "product.initiative.stage_changed")
    product_deployed_topic: str = os.environ.get("AB_PRODUCT_DEPLOYED_TOPIC", "product.initiative.deployed")
    # OIDC (Keycloak). Defaults target the host-published port for tests; in-container
    # services override these to reach Keycloak by service name (see docker-compose).
    oidc_token_url: str = os.environ.get(
        "AB_OIDC_TOKEN_URL", "http://localhost:18083/realms/ab/protocol/openid-connect/token"
    )
    oidc_jwks_url: str = os.environ.get(
        "AB_OIDC_JWKS_URL", "http://localhost:18083/realms/ab/protocol/openid-connect/certs"
    )
    # iss is the fixed Keycloak frontend URL (same string host or in-container, since
    # KC_HOSTNAME pins it); aud is set by an audience mapper on each client.
    oidc_issuer: str = os.environ.get("AB_OIDC_ISSUER", "http://localhost:18083/realms/ab")
    oidc_audience: str = os.environ.get("AB_OIDC_AUDIENCE", "ab-gateway")
    # Vault (dev) holds agent client secrets. Host default for tests; in-container
    # services override AB_VAULT_ADDR to reach Vault by service name.
    vault_addr: str = os.environ.get("AB_VAULT_ADDR", "http://localhost:18200")
    vault_token: str = _secret("AB_VAULT_TOKEN", "root")  # unwraps agent client secrets
    # Shared secret the intervention services (console, kill-switch) use to verify the reverse
    # proxy's signed operator-identity headers (VULN-001/004).
    operator_auth_secret: str = _secret("AB_OPERATOR_AUTH_SECRET", "dev-insecure-operator-secret")
    # Key for the audit hash chain's HMAC (VULN-006). Held outside the DB so a DB-write adversary
    # cannot re-forge the chain. A real deployment stores it in Vault/KMS, separate from Postgres.
    audit_hmac_key: str = _secret("AB_AUDIT_HMAC_KEY", "dev-insecure-audit-key")


settings = Settings()
