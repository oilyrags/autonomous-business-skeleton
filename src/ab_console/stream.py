"""Live event streaming (SSE): surface the bus to the operator in real time. The formatting is
pure; the event *source* is an injectable provider — the stub replays sample decision events (and
ends, so tests and curls terminate), while a live deployment plugs a bus consumer into the same
seam. Server-Sent Events + the browser's native EventSource: no client framework, no toolchain.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator


def sse_format(events: Iterable[dict[str, object]]) -> Iterator[str]:
    """Render events as SSE frames (`data: {json}\\n\\n`) — what EventSource consumes."""
    for event in events:
        yield f"data: {json.dumps(event, separators=(',', ':'))}\n\n"


SAMPLE_EVENTS: list[dict[str, object]] = [
    {
        "eventName": "AgentDecisionMade",
        "decisionId": "dec-101",
        "agentId": "executive.cmo_agent",
        "authorityLevel": 2,
        "approvalStatus": "autonomous_within_policy",
        "businessId": "rocket",
    },
    {
        "eventName": "ExperimentConcluded",
        "experimentId": "exp-cta-1",
        "action": "scale",
        "businessId": "rocket",
    },
    {
        "eventName": "LedgerEntryPosted",
        "txnId": "txn_9f2",
        "amountMinor": 40000,
        "payee": "supplier",
        "businessId": "rocket",
    },
    {
        "eventName": "ContentPublished",
        "platform": "linkedin",
        "platformPostId": "linkedin_rocket_7",
        "businessId": "rocket",
    },
    {
        "eventName": "CapitalReallocationRecommended",
        "action": "sunset",
        "capitalDelta": -200000,
        "businessId": "sinker",
    },
]
