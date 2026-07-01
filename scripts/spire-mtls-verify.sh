#!/usr/bin/env bash
# Verify a LIVE request routes over SPIFFE mTLS to the real gateway:
#   host -> agent-proxy (plaintext) -> [mTLS, SVID-authorized] -> gateway-proxy -> gateway
# Requires: app stack up (`make up`), SPIRE up (`make spire-up`), proxies up (`make spire-mtls`).
set -euo pipefail

echo "=== positive: request via agent-proxy reaches the gateway over mTLS ==="
ok=""
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:18091/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 2
done
[ -n "$ok" ] || { echo "FAIL: agent-proxy path never became ready"; exit 1; }
resp=$(curl -fsS http://localhost:18091/health)
echo "gateway /health via mTLS: $resp"
echo "$resp" | python3 -c "import sys, json; assert json.load(sys.stdin)['status'] == 'ok', 'bad body'"

echo "=== negative: direct TLS to gateway-proxy WITHOUT an SVID is rejected ==="
if curl -fsS -k --max-time 5 https://localhost:18443/health >/dev/null 2>&1; then
  echo "UNEXPECTED: no-cert client was accepted"; exit 1
else
  echo "no-cert client rejected (expected)"
fi

echo "spire-mtls-verify: PASS"
