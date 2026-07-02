"""Icinga2 REST submit adapter: payload building + submit via an injected client (pure, infra-free)."""

from __future__ import annotations

from typing import Any

from ab_monitor.check import CheckResult, CheckStatus, Perfdatum
from ab_monitor.icinga2 import Icinga2RestExporter


class _RecordingClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, *, json: dict[str, Any], headers: dict[str, str]) -> Any:
        self.calls.append({"url": url, "json": json, "headers": headers})
        return None


def _exporter(client: _RecordingClient) -> Icinga2RestExporter:
    return Icinga2RestExporter("https://icinga2:5665", "api", "secret", client=client)


def test_payload_maps_status_output_and_perfdata() -> None:
    result = CheckResult(
        "gateway-mtls",
        CheckStatus.CRITICAL,
        "cert expires in 9 days",
        (Perfdatum("days", 9, 30, 14),),
    )
    body = _exporter(_RecordingClient()).payload(result)
    assert body["exit_status"] == 2
    assert body["plugin_output"] == "CRITICAL: cert expires in 9 days"
    assert body["performance_data"] == ["days=9;30;14"]
    assert 'service.name=="gateway-mtls"' in body["filter"]


def test_per_business_check_targets_the_business_host() -> None:
    result = CheckResult("hog-health", CheckStatus.CRITICAL, "operating loss", business_id="hog")
    body = _exporter(_RecordingClient()).payload(result)
    assert 'host.name=="hog"' in body["filter"]  # per-business host


def test_platform_check_targets_the_default_host() -> None:
    result = CheckResult("gateway-up", CheckStatus.OK, "responding")  # no business_id
    body = _exporter(_RecordingClient()).payload(result)
    assert 'host.name=="autonomous-business"' in body["filter"]


def test_export_posts_one_request_per_result_to_the_action_url() -> None:
    client = _RecordingClient()
    results = [
        CheckResult("gateway-up", CheckStatus.OK, "responding"),
        CheckResult("agent-up", CheckStatus.CRITICAL, "down"),
    ]
    _exporter(client).export(results)
    assert len(client.calls) == 2
    assert all(c["url"].endswith("/v1/actions/process-check-result") for c in client.calls)
