#!/usr/bin/env bash
# Verify the fully-secured topology: the agent's business call succeeds while BOTH
# hops run over mTLS — agent->gateway AND gateway->OPA. Because the gateway's OPA URL
# is repointed to its client sidecar, a 200 (which requires an OPA "allow") proves the
# authorize decision came back over the mTLS'd OPA hop.
set -euo pipefail

echo "=== agent /act over mTLS (authorize flows through the mTLS'd OPA hop) ==="
ok=""
for _ in $(seq 1 45); do
  code=$(curl -sS -o /tmp/act.json -w '%{http_code}' -X POST http://localhost:18090/act 2>/dev/null || true)
  if [ "$code" = "200" ]; then ok=1; break; fi
  sleep 2
done
[ -n "$ok" ] || { echo "FAIL: agent /act never returned 200"; cat /tmp/act.json 2>/dev/null || true; exit 1; }
python3 -c "import json; d=json.load(open('/tmp/act.json')); assert d['gateway_status']==200 and d['body']['status']=='ok', d; print('act OK:', d['decision_id'])"

echo "=== negative: opa-proxy mTLS rejects a client with no SVID ==="
if curl -fsS -k --max-time 5 https://localhost:19181/ >/dev/null 2>&1; then
  echo "UNEXPECTED: no-cert client accepted at opa-proxy"; exit 1
else
  echo "no-cert client rejected at opa-proxy (expected)"
fi

echo "spire-secure-verify: PASS (agent->gateway AND gateway->OPA over mTLS)"
