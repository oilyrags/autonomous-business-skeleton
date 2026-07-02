"""Console render smoke (deterministic, no infra).

    uv run python -m ab_console

Renders the Fleet Dashboard through the design system (daisyUI + Tailwind, vendored) via TestClient
and prints a terse summary — proves view-model → template → assets end to end. `make console-serve`
runs it live.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from ab_console.app import app
from ab_console.auth import sign_identity


def main() -> int:
    # The console requires an authenticated operator (VULN-001); the trusted proxy signs the
    # identity headers — the smoke does the same so it exercises the real auth path.
    op = {
        "X-Operator-Id": "smoke.operator",
        "X-Operator-Role": "operator",
        "X-Operator-Sig": sign_identity("smoke.operator", "operator"),
    }
    with TestClient(app, headers=op) as client:
        page = client.get("/")
        css = client.get("/static/console.css")
        daisy = client.get("/static/vendor/daisyui.css")
        tailwind = client.get("/static/vendor/tailwind-browser.js")
    ok = all(r.status_code == 200 for r in (page, css, daisy, tailwind))
    badges = page.text.count('class="badge')
    print(
        f"  GET /                            -> {page.status_code} ({len(page.text)} bytes, {badges} badges)"
    )
    print(f"  GET /static/console.css          -> {css.status_code} ({len(css.text)} bytes, custom layer)")
    print(f"  GET /static/vendor/daisyui.css   -> {daisy.status_code} ({len(daisy.text)} bytes)")
    print(f"  GET /static/vendor/tailwind*.js  -> {tailwind.status_code} ({len(tailwind.text)} bytes)")
    print(f"\n  fleet dashboard render: {'OK' if ok else 'FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
