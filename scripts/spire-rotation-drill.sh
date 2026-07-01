#!/usr/bin/env bash
# SVID rotation drill: with a short SVID TTL, prove the workload SVID actually
# rotates AND the agent->gateway mTLS path keeps serving with zero downtime.
# Requires: app stack up (`make up`) + short-TTL SPIRE + proxies (via `make spire-rotation-drill`).
set -euo pipefail

SOCK="/opt/spire/sockets/agent.sock"
DRILL_SECONDS="${DRILL_SECONDS:-80}"

gateway_svid_serial() {
  docker compose exec -T -u 1002 spire-agent sh -c \
    "rm -rf /tmp/rot && mkdir -p /tmp/rot && spire-agent api fetch x509 -socketPath $SOCK -write /tmp/rot >/dev/null 2>&1 && openssl x509 -in /tmp/rot/svid.0.pem -noout -serial" \
    | sed 's/serial=//' | tr -d '\r'
}

# wait for the mTLS path to be ready
for _ in $(seq 1 30); do curl -fsS http://localhost:18091/health >/dev/null 2>&1 && break; sleep 2; done

s1=$(gateway_svid_serial)
echo "gateway SVID serial #1: $s1"

echo "=== ${DRILL_SECONDS}s zero-downtime check across rotation (health every 2s over mTLS) ==="
ok=0; fail=0; end=$((SECONDS + DRILL_SECONDS))
while [ "$SECONDS" -lt "$end" ]; do
  if curl -fsS --max-time 3 http://localhost:18091/health >/dev/null 2>&1; then ok=$((ok + 1)); else fail=$((fail + 1)); fi
  sleep 2
done

s2=$(gateway_svid_serial)
echo "gateway SVID serial #2: $s2"
echo "requests: ok=$ok fail=$fail"
echo "=== ghostunnel certificate-reload events ==="
docker compose --profile spiffe logs gateway-proxy 2>&1 | grep -iE 'certificate|reload|rotat|renew|updated' | tail -3 || true

[ "$s1" != "$s2" ] || { echo "FAIL: SVID serial did not change — no rotation observed"; exit 1; }
[ "$fail" -eq 0 ]   || { echo "FAIL: $fail requests failed during rotation (not zero-downtime)"; exit 1; }
echo "spire-rotation-drill: PASS (SVID rotated ${s1} -> ${s2}, ${ok}/${ok} requests ok across rotation)"
