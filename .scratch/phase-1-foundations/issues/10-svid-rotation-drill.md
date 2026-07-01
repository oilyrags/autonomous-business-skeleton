# 10 — SVID rotation drill (zero-downtime mTLS)

Status: done

## What to build

Demonstrate the core SPIFFE benefit: short-lived, auto-rotating SVIDs with zero downtime
on the agent→gateway mTLS path.

## Acceptance criteria

- [x] Run the mTLS path with a short SVID TTL (60s).
- [x] Prove the workload SVID actually rotates (serial changes) within the drill window.
- [x] Prove the mTLS path serves continuously across the rotation (0 failed requests over
      a window longer than the TTL, so the original SVID expires mid-drill).

## Comments

**Done (2026-07-01).** `scripts/spire-bootstrap.sh` gained a `SVID_TTL` param (`-x509SVIDTTL`
on the workload entries); `scripts/spire-rotation-drill.sh` records the gateway SVID serial,
hammers `/health` over mTLS every 2s for 80s, then re-reads the serial. `make spire-rotation-drill`
brings up short-TTL (60s) SPIRE + proxies and runs it.

Result: SVID serial rotated `4C9C52BF…` → `5D641786…`; **40/40** requests over mTLS succeeded
across the 80s window (> the 60s TTL, so the first SVID expired mid-drill) → ghostunnel picked
up the fresh SVID from the Workload API with **zero downtime**.

Kept as a runnable drill (`make spire-rotation-drill`), not a CI step (80s). The mTLS path
itself is already CI-verified (slice 09).

## Blocked by

- 09 — Route agent→gateway over mTLS
