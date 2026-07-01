#!/usr/bin/env bash
# Bootstrap SPIRE: node-alias join token + workload registration entries
# (gateway=uid 1002, agent=uid 1001), then start the agent with the token.
# Idempotent enough for repeated runs (entries are recreated; a fresh token is issued).
set -euo pipefail

DC="docker compose"
SVR="$DC exec -T spire-server spire-server"
SVID_TTL="${SVID_TTL:-3600}"   # X509-SVID TTL (seconds); short values drive the rotation drill

$DC up -d --build --wait spire-server

TOKEN=$($SVR token generate -spiffeID spiffe://ab.internal/node -ttl 3600 | sed -n 's/^Token: *//p' | tr -d '\r')
[ -n "$TOKEN" ] || { echo "failed to obtain join token" >&2; exit 1; }

$SVR entry create -parentID spiffe://ab.internal/node -spiffeID spiffe://ab.internal/gateway \
  -selector unix:uid:1002 -x509SVIDTTL "$SVID_TTL" >/dev/null 2>&1 || true
$SVR entry create -parentID spiffe://ab.internal/node -spiffeID spiffe://ab.internal/agent \
  -selector unix:uid:1001 -x509SVIDTTL "$SVID_TTL" >/dev/null 2>&1 || true
$SVR entry create -parentID spiffe://ab.internal/node -spiffeID spiffe://ab.internal/opa \
  -selector unix:uid:1003 -x509SVIDTTL "$SVID_TTL" >/dev/null 2>&1 || true
$SVR entry create -parentID spiffe://ab.internal/node -spiffeID spiffe://ab.internal/postgres \
  -selector unix:uid:1004 -x509SVIDTTL "$SVID_TTL" >/dev/null 2>&1 || true

$DC exec -T spire-server sh -c "printf '%s' '$TOKEN' > /opt/spire/sockets/jointoken"
$DC rm -sf spire-agent >/dev/null 2>&1 || true
$DC up -d spire-agent

echo "spire bootstrapped (token ${TOKEN:0:8}...)"
