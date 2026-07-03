"""Per-port adapter selection (PRD 0009 S1 / ADR-0061).

A live deployment selects the stub or a real adapter **per port** via ``AB_<PORT>_PROVIDER`` —
generalizing the one precedent (``ab_gateway.providers.served()`` reading ``AB_MODEL_PROVIDER``).
Unset defaults to the stub, so infra-free CI and dev keep working unchanged; a ``critical`` seam
(money / egress / identity) refuses to run on the stub outside a dev environment (fail-closed, the
VULN-005 posture). Stubs are never deleted — they remain the CI default behind the same seam.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from typing import TypeVar

from ab_common.config import is_dev_env

T = TypeVar("T")


def select_adapter(
    port_name: str,
    *,
    stub: Callable[[], T],
    real: Mapping[str, Callable[[], T]],
    critical: bool = False,
) -> T:
    """Return the adapter selected by ``AB_<PORT_NAME>_PROVIDER``: ``"stub"`` (or unset) → the stub;
    a key in ``real`` → that real adapter. A ``critical`` port left on the stub outside a dev
    environment raises (a money/egress/identity seam must not silently run on a stub in prod). An
    unknown provider name raises rather than silently falling back."""
    key = f"AB_{port_name.upper()}_PROVIDER"
    choice = os.environ.get(key, "stub").strip().lower()
    if choice == "stub":
        if critical and not is_dev_env():
            raise RuntimeError(
                f"{key} must select a real adapter ({sorted(real)}) when AB_ENV is not a dev environment"
            )
        return stub()
    if choice in real:
        return real[choice]()
    known = ", ".join(["stub", *sorted(real)])
    raise RuntimeError(f"{key}={choice!r} is not a known provider (expected one of: {known})")
