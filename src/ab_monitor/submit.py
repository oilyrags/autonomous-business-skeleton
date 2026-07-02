"""Submit the check suite to a live Icinga2 via its REST API (operator command, not CI).

    ICINGA2_API_PASSWORD=... uv run python -m ab_monitor.submit

Reads connection config from the environment and submits each CheckResult as an Icinga2 passive
check result. Requires the monitoring profile up (`docker compose -f docker-compose.monitoring.yml
up -d`). Fails clearly if `ICINGA2_API_PASSWORD` is unset.
"""

from __future__ import annotations

import os

from ab_monitor.icinga2 import Icinga2RestExporter
from ab_monitor.suite import demo_suite


def main() -> int:
    password = os.environ.get("ICINGA2_API_PASSWORD")
    if not password:
        print("ICINGA2_API_PASSWORD is required (the monitoring profile's API password)")
        return 2
    exporter = Icinga2RestExporter(
        os.environ.get("ICINGA2_URL", "https://localhost:5665"),
        os.environ.get("ICINGA2_API_USER", "api"),
        password,
        verify=os.environ.get("ICINGA2_VERIFY", "false").lower() == "true",
    )
    results = demo_suite()
    exporter.export(results)
    print(f"submitted {len(results)} check results to Icinga2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
