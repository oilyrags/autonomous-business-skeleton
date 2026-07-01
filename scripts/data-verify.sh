#!/usr/bin/env bash
# Verify the running data service (Phase 2) as a live semantic layer: drive real
# AgentDecisionMade events through the mTLS'd agent->gateway path, then prove the
# data service consumed them off the bus, rebuilt the warehouse, and now serves the
# canonical KPIs over HTTP. A nonzero decisions_recorded_total that reflects the
# decisions we just drove proves the whole event -> warehouse -> metric loop end-to-end.
set -euo pipefail

DATA=http://localhost:18085
AGENT=http://localhost:18090
DRIVE=${DRIVE:-3}

echo "=== data service lists the canonical metrics registry ==="
curl -fsS "$DATA/metrics" | python3 -c "
import sys, json
names = {m['name'] for m in json.load(sys.stdin)}
need = {'decisions_recorded_total', 'deciding_agents_total'}
assert need <= names, f'missing metrics: {need - names}'
print('metrics registry OK:', sorted(names))
"

echo "=== drive $DRIVE decisions through the agent (agent->gateway over mTLS -> bus) ==="
before=$(curl -fsS "$DATA/metrics/decisions_recorded_total" \
  | python3 -c "import sys, json; v=json.load(sys.stdin)['value']; print(v if v is not None else 0)")
echo "decisions_recorded_total before = $before"
for _ in $(seq 1 "$DRIVE"); do
  curl -fsS -X POST "$AGENT/act" \
    | python3 -c "import sys, json; d=json.load(sys.stdin); assert d['gateway_status']==200, d"
done
echo "drove $DRIVE decisions"

echo "=== data service consumes the bus, rebuilds the warehouse, serves the new count ==="
target=$((before + DRIVE))
ok=""
for _ in $(seq 1 45); do
  val=$(curl -fsS "$DATA/metrics/decisions_recorded_total" \
    | python3 -c "import sys, json; v=json.load(sys.stdin)['value']; print(v if v is not None else 0)")
  if [ "$val" -ge "$target" ]; then ok=1; echo "decisions_recorded_total = $val (>= $target)"; break; fi
  sleep 2
done
[ -n "$ok" ] || { echo "FAIL: decisions_recorded_total never reached $target"; exit 1; }

echo "=== deciding_agents_total is a live, nonzero canonical KPI ==="
curl -fsS "$DATA/metrics/deciding_agents_total" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['value'] and d['value'] >= 1, d
print('deciding_agents_total =', d['value'], '(grain:', d['grain'] + ')')
"

echo "=== negative: an unknown metric is a 404, not a fabricated number ==="
code=$(curl -sS -o /dev/null -w '%{http_code}' "$DATA/metrics/not_a_real_metric")
[ "$code" = "404" ] || { echo "FAIL: expected 404 for unknown metric, got $code"; exit 1; }
echo "unknown metric -> 404 (expected)"

echo "data-verify: PASS (data service serves canonical KPIs from live bus events)"
