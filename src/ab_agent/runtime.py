"""agent runtime — the accountable AI principal.

Obtains a token and acts by calling the gateway tool-call API. The HTTP client is
injected (a real httpx client in deployment, a TestClient in tests) so the agent's
code path is exercised the same way everywhere.
"""

from typing import Any, Protocol


class HttpClient(Protocol):
    def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> Any: ...


def record_decision(
    http: HttpClient, token: str, decision: dict[str, Any], purpose: str = "record a material decision"
) -> Any:
    """Call the gateway to record a decision. Returns the HTTP response."""
    return http.post(
        "/tool-call",
        headers={"Authorization": f"Bearer {token}"},
        json={"tool": "decision_registry.write", "args": decision, "purpose": purpose},
    )
