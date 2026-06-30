# `src/` — walking-skeleton code

Python monorepo for Phase 1 (see [`/docs/prd/0001-phase-1-foundations-walking-skeleton.md`](../docs/prd/0001-phase-1-foundations-walking-skeleton.md) and ADR-0001/0002/0003). One distribution, six packages:

| Package | Role |
|---|---|
| `ab_schemas` | Shared Pydantic event/data models (match `architecture/events.asyncapi.yaml`). No business logic. |
| `ab_identity` | Issues / validates / revokes short-lived agent JWTs (interim issuer, ADR-0003). |
| `ab_gateway` | Single ingress: token validation, (stub) model routing, OPA authZ, kill-switch check, tool dispatch, event + audit emit. Determinism boundary. |
| `ab_killswitch` | Control flags + revocation + publishes `KillSwitchActivated`. Launch-blocker control. |
| `ab_audit` | Append-only hash-chained audit writer + read API + `AgentDecisionMade` consumer. |
| `ab_agent` | The accountable AI principal runtime. |

## Commands (from repo root)

```bash
make sync       # install workspace (uv)
make up         # local stack: OPA + Redpanda + Postgres (+ service placeholders)
make test       # pytest
make check      # lint + typecheck + test (what CI runs)
make down       # tear down stack
```

## Status

- **Slice 00 (scaffold):** done — toolchain, packages, infra compose, CI, `ab_schemas` with `AgentDecisionMade`/`KillSwitchActivated` + passing round-trip test.
- **Slices 01–04:** see [`/.scratch/phase-1-foundations/issues/`](../.scratch/phase-1-foundations/issues/).
