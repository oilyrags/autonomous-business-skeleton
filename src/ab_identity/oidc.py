"""Obtain agent tokens from Keycloak via the OIDC client-credentials grant."""

import httpx

from ab_common.config import settings


def fetch_token(client_id: str, client_secret: str, token_url: str | None = None) -> str:
    resp = httpx.post(
        token_url or settings.oidc_token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])
