"""Runtime configuration, read from the environment with local-dev defaults.

Defaults target the local docker-compose stack (ports published on localhost).
"""

import os


class Settings:
    pg_dsn: str = os.environ.get("AB_PG_DSN", "postgresql://ab:ab@localhost:55432/ab")
    opa_url: str = os.environ.get("AB_OPA_URL", "http://localhost:8181")
    kafka_bootstrap: str = os.environ.get("AB_KAFKA", "localhost:19092")
    decision_topic: str = os.environ.get("AB_DECISION_TOPIC", "executive.decision.made")
    kill_topic: str = os.environ.get("AB_KILL_TOPIC", "security.killswitch.activated")
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
    vault_token: str = os.environ.get("AB_VAULT_TOKEN", "root")


settings = Settings()
