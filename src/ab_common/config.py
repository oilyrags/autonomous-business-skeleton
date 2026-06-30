"""Runtime configuration, read from the environment with local-dev defaults.

Defaults target the local docker-compose stack (ports published on localhost).
"""

import os


class Settings:
    pg_dsn: str = os.environ.get("AB_PG_DSN", "postgresql://ab:ab@localhost:55432/ab")
    opa_url: str = os.environ.get("AB_OPA_URL", "http://localhost:8181")
    kafka_bootstrap: str = os.environ.get("AB_KAFKA", "localhost:19092")
    jwt_secret: str = os.environ.get("AB_JWT_SECRET", "dev-secret-change-me-in-prod-0123456789abcdef")
    jwt_alg: str = "HS256"
    decision_topic: str = os.environ.get("AB_DECISION_TOPIC", "executive.decision.made")
    kill_topic: str = os.environ.get("AB_KILL_TOPIC", "security.killswitch.activated")


settings = Settings()
