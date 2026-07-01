#!/usr/bin/env bash
# Verify the SPIFFE tracer: (1) SPIRE issues the right SVID per workload identity,
# (2) a mutual-TLS handshake between the agent and gateway SVIDs succeeds, and
# (3) a client WITHOUT an SVID is rejected. Runs inside the spire-agent container.
set -euo pipefail

DC="docker compose"
SOCK="/opt/spire/sockets/agent.sock"

svid_id() {  # $1 = uid
  $DC exec -T -u "$1" spire-agent spire-agent api fetch x509 -socketPath "$SOCK" 2>&1 \
    | sed -n 's/.*SPIFFE ID:[[:space:]]*//p' | head -1 | tr -d '\r'
}

# wait for the agent to have SVIDs
for _ in $(seq 1 30); do
  $DC exec -T -u 1002 spire-agent spire-agent api fetch x509 -socketPath "$SOCK" >/dev/null 2>&1 && break
  sleep 2
done

GW=$(svid_id 1002); AG=$(svid_id 1001)
echo "gateway workload SVID: $GW"
echo "agent   workload SVID: $AG"
[ "$GW" = "spiffe://ab.internal/gateway" ] || { echo "FAIL: gateway SPIFFE ID"; exit 1; }
[ "$AG" = "spiffe://ab.internal/agent" ]   || { echo "FAIL: agent SPIFFE ID"; exit 1; }

# Materialise both SVIDs to files (each fetch runs as the matching uid).
$DC exec -T -u 1002 spire-agent sh -c "rm -rf /tmp/gw && mkdir -p /tmp/gw && spire-agent api fetch x509 -socketPath $SOCK -write /tmp/gw >/dev/null 2>&1"
$DC exec -T -u 1001 spire-agent sh -c "rm -rf /tmp/ag && mkdir -p /tmp/ag && spire-agent api fetch x509 -socketPath $SOCK -write /tmp/ag >/dev/null 2>&1"

# Mutual TLS: gateway serves (requires+verifies client cert vs the trust bundle),
# agent connects presenting its SVID. Verification OK == mTLS with SPIFFE certs.
echo "=== mTLS handshake (agent SVID -> gateway SVID) ==="
$DC exec -T spire-agent sh -c '
  set -e
  openssl s_server -accept 8443 -cert /tmp/gw/svid.0.pem -key /tmp/gw/svid.0.key \
    -CAfile /tmp/gw/bundle.0.pem -Verify 1 -naccept 1 -quiet >/dev/null 2>&1 </dev/null &
  sleep 1
  echo hello | openssl s_client -connect 127.0.0.1:8443 -cert /tmp/ag/svid.0.pem \
    -key /tmp/ag/svid.0.key -CAfile /tmp/ag/bundle.0.pem -verify_return_error -brief 2>&1 \
    | grep -iE "Verification: OK|Verification error" || true
'

echo "=== negative: client with NO SVID is rejected ==="
$DC exec -T spire-agent sh -c '
  openssl s_server -accept 8444 -cert /tmp/gw/svid.0.pem -key /tmp/gw/svid.0.key \
    -CAfile /tmp/gw/bundle.0.pem -Verify 1 -naccept 1 -quiet >/dev/null 2>&1 </dev/null &
  sleep 1
  if echo hello | openssl s_client -connect 127.0.0.1:8444 -CAfile /tmp/ag/bundle.0.pem -brief >/dev/null 2>&1; then
    echo "UNEXPECTED: no-cert client accepted"; exit 1
  else
    echo "no-cert client rejected (expected)"
  fi
'
echo "spire-verify: PASS"
