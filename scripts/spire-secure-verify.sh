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

echo "=== audit service reads its DB over mTLS (audit-pg-proxy) ==="
curl -fsS "http://localhost:18081/audit?action=decision_registry.write" \
  | python3 -c "import sys, json; rows=json.load(sys.stdin); assert any(r['outcome']=='allow' for r in rows), rows; print('audit read OK:', len(rows), 'record(s)')"

echo "=== killswitch service writes its DB over mTLS (killswitch-pg-proxy) ==="
curl -fsS -X POST http://localhost:18002/activate -H 'Content-Type: application/json' \
  -d '{"scope":"agent","target_id":"spiffe-drill-test","reason":"mtls drill","activated_by":"verify"}' \
  | python3 -c "import sys, json; d=json.load(sys.stdin); assert d['status']=='activated', d; print('killswitch write OK')"

echo "=== negative: proxies reject a client with no SVID ==="
for hostport in "opa-proxy:19181" "postgres-proxy:16432"; do
  name=${hostport%%:*}; port=${hostport##*:}
  if curl -fsS -k --max-time 5 "https://localhost:${port}/" >/dev/null 2>&1; then
    echo "UNEXPECTED: no-cert client accepted at ${name}"; exit 1
  else
    echo "no-cert client rejected at ${name} (expected)"
  fi
done

echo "=== negative: gateway has NO direct route to Postgres (network-isolated) ==="
if docker compose exec -T gateway python -c \
    "import socket; socket.create_connection(('postgres', 5432), 3)" >/dev/null 2>&1; then
  echo "UNEXPECTED: gateway reached postgres:5432 directly"; exit 1
else
  echo "gateway cannot reach postgres directly (expected — only via mTLS proxy)"
fi

echo "spire-secure-verify: PASS (all hops + DB clients over mTLS; Postgres network-isolated)"
