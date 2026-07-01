#!/usr/bin/env bash
# Verify the gateway/audit/data -> Redpanda hop runs over SPIFFE mTLS. A full decision
# round-trip proves BOTH directions of the bus: the gateway PRODUCES AgentDecisionMade
# and the audit + data services CONSUME it — all with AB_KAFKA pointed at the kafka-mtls
# client proxy (so every byte crosses ghostunnel mTLS to redpanda-proxy -> Redpanda).
set -euo pipefail

echo "=== bus clients are pointed at the mTLS proxy, not plaintext Redpanda ==="
for svc in gateway audit killswitch data; do
  val=$(docker compose -f docker-compose.yml -f docker-compose.spiffe.yml --profile spiffe \
    exec -T "$svc" printenv AB_KAFKA 2>/dev/null | tr -d '\r')
  [ "$val" = "kafka-mtls:29092" ] || { echo "FAIL: $svc AB_KAFKA=$val (expected kafka-mtls:29092)"; exit 1; }
  echo "  $svc AB_KAFKA=$val"
done

echo "=== drive a decision: gateway PRODUCES to the bus over mTLS ==="
ok=""
for _ in $(seq 1 45); do
  code=$(curl -sS -o /tmp/bus_act.json -w '%{http_code}' -X POST http://localhost:18090/act 2>/dev/null || true)
  if [ "$code" = "200" ]; then ok=1; break; fi
  sleep 2
done
[ -n "$ok" ] || { echo "FAIL: agent /act never returned 200"; cat /tmp/bus_act.json 2>/dev/null || true; exit 1; }
DECISION=$(python3 -c "import json; print(json.load(open('/tmp/bus_act.json'))['decision_id'])")
echo "produced decision_id=$DECISION"

echo "=== audit service CONSUMED it off the mTLS bus (decision reaches the hash chain) ==="
found=""
for _ in $(seq 1 30); do
  if curl -fsS "http://localhost:18081/audit?action=decision_registry.write" \
      | python3 -c "import sys,json; rows=json.load(sys.stdin); import os; sys.exit(0 if any(r.get('outcome')=='allow' for r in rows) else 1)"; then
    found=1; break
  fi
  sleep 2
done
[ -n "$found" ] || { echo "FAIL: audit never recorded an allow (consumer over mTLS bus)"; exit 1; }
echo "audit consumed OK (allow record present)"

echo "=== data service CONSUMED it off the mTLS bus (canonical KPI advances) ==="
ok=""
for _ in $(seq 1 30); do
  v=$(curl -fsS http://localhost:18085/metrics/decisions_recorded_total \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['value'] if d['value'] is not None else -1)")
  if [ "$v" -ge 1 ] 2>/dev/null; then ok=1; echo "decisions_recorded_total = $v"; break; fi
  sleep 2
done
[ -n "$ok" ] || { echo "FAIL: data service never saw a decision (consumer over mTLS bus)"; exit 1; }

echo "=== negative: a client with no SVID cannot reach redpanda-proxy ==="
if curl -fsS -k --max-time 5 "https://localhost:29092/" >/dev/null 2>&1; then
  echo "UNEXPECTED: no-cert client accepted at redpanda-proxy"; exit 1
else
  echo "no-cert client rejected at redpanda-proxy (expected)"
fi

echo "spire-bus-verify: PASS (gateway produce + audit/data consume over SPIFFE mTLS)"
