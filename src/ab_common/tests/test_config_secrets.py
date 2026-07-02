"""Secret-bearing settings are fail-closed outside dev (VULN-005): a weak default is used only in a
dev environment; elsewhere an unset secret refuses to start. Exercised in a fresh interpreter so the
import-time behaviour is what's actually tested (and no global config state leaks between tests)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parents[2])  # .../src on PYTHONPATH for the child interpreter
_PROBE = "import ab_common.config as c; print(c.settings.operator_auth_secret)"


def _run(**env_overrides: str) -> subprocess.CompletedProcess[str]:
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": _SRC}
    # start from a clean slate, then apply the case's overrides
    for var in ("AB_ENV", "AB_VAULT_TOKEN", "AB_PG_DSN", "AB_OPERATOR_AUTH_SECRET"):
        env.pop(var, None)
    env.update(env_overrides)
    return subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True, env=env)


def test_dev_env_uses_convenience_defaults() -> None:
    result = _run(AB_ENV="dev")
    assert result.returncode == 0
    assert result.stdout.strip() == "dev-insecure-operator-secret"


def test_production_refuses_a_missing_secret() -> None:
    result = _run(AB_ENV="production", AB_VAULT_TOKEN="x", AB_PG_DSN="postgresql://u:p@db/ab")
    assert result.returncode != 0  # import fails closed
    assert "AB_OPERATOR_AUTH_SECRET must be set" in result.stderr


def test_production_accepts_explicit_secrets() -> None:
    result = _run(
        AB_ENV="production",
        AB_PG_DSN="postgresql://u:p@db/ab",
        AB_VAULT_TOKEN="s.real",
        AB_OPERATOR_AUTH_SECRET="a-real-long-secret",
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "a-real-long-secret"
