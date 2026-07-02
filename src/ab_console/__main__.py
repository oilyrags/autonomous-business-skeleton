"""Console render smoke (deterministic, no infra).

    uv run python -m ab_console

Renders the Fleet Dashboard through the design system via TestClient and prints a terse summary —
proves the view-model → template → CSS path end to end. `make console-serve` runs it live.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from ab_console.app import app


def main() -> int:
    with TestClient(app) as client:
        page = client.get("/")
        css = client.get("/static/console.css")
    ok = page.status_code == 200 and css.status_code == 200
    rows = page.text.count('class="pill')
    print(f"  GET /                 -> {page.status_code} ({len(page.text)} bytes, {rows} status pills)")
    print(f"  GET /static/console.css -> {css.status_code} ({len(css.text)} bytes)")
    print(f"\n  fleet dashboard render: {'OK' if ok else 'FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
