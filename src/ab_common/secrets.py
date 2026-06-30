"""Read agent client secrets from Vault (KV v2). Secrets are not held in app env.

Seeded at ``secret/ab/clients`` (see `make seed-vault`). Cached per process.
"""

import httpx

from ab_common.config import settings

_cache: dict[str, str] | None = None


def _load() -> dict[str, str]:
    global _cache
    if _cache is None:
        resp = httpx.get(
            f"{settings.vault_addr}/v1/secret/data/ab/clients",
            headers={"X-Vault-Token": settings.vault_token},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()["data"]["data"]
        _cache = {str(k): str(v) for k, v in data.items()}
    assert _cache is not None
    return _cache


def get_client_secret(client_id: str) -> str:
    return _load()[client_id]
