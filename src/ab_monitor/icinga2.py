"""A real NagiosExporter adapter: submits check results to Icinga2 via its process-check-result
REST API. Same vendor-neutral CheckResults as the stub — only the destination changes. The payload
builder is pure (CI-tested); the HTTP client is injectable so the network submit is the only part
that needs a live Icinga2 (M4 integration test skips without it). A classic-Nagios NSCA adapter is
the alternative behind the same port.
"""

from __future__ import annotations

from typing import Any, Protocol

from ab_monitor.check import CheckResult

_ACTION_PATH = "/v1/actions/process-check-result"


class PostClient(Protocol):
    """The slice of an HTTP client this adapter needs (matches ``httpx.Client``)."""

    def post(self, url: str, *, json: dict[str, Any], headers: dict[str, str]) -> Any: ...


class Icinga2RestExporter:
    """Submit each CheckResult as an Icinga2 passive check result. A Service is targeted by
    ``host.name`` (the business_id, or a default platform host) + ``service.name`` (the check name).
    """

    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        *,
        host: str = "autonomous-business",
        verify: bool = True,
        client: PostClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = (user, password)
        self._host = host
        self._verify = verify
        self._client = client  # injected in tests; built lazily otherwise

    def payload(self, result: CheckResult) -> dict[str, Any]:
        """The Icinga2 process-check-result body for one check (pure — no I/O)."""
        host = result.business_id or self._host
        return {
            "type": "Service",
            "filter": f'host.name=="{host}" && service.name=="{result.name}"',
            "exit_status": int(result.status),
            "plugin_output": f"{result.status.name}: {result.output}",
            "performance_data": [p.render() for p in result.perfdata],
        }

    def export(self, results: list[CheckResult]) -> None:
        client = self._client or self._build_client()
        url = f"{self._base_url}{_ACTION_PATH}"
        for result in results:
            client.post(url, json=self.payload(result), headers={"Accept": "application/json"})

    def _build_client(self) -> PostClient:
        import httpx  # lazy: only needed for a real submit

        client: PostClient = httpx.Client(auth=self._auth, verify=self._verify, timeout=5.0)
        return client
