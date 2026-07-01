# Authorization for the walking skeleton. Default-deny; the skeleton agent may
# only write decisions. The gateway queries POST /v1/data/ab/authz/allow with
# input {principal, action, resource, purpose}.
package ab.authz

import rego.v1

default allow := false

# Slice 01: the skeleton agent may record decisions.
allow if {
	input.action == "decision_registry.write"
	input.principal == "executive.cmo_agent"
}

# Slice 25: the skeleton agent may send external notifications. Policy authorizes the
# capability; the gateway's egress guard still blocks over-classified data (exfiltration).
allow if {
	input.action == "notify.external"
	input.principal == "executive.cmo_agent"
}

# Slice 30: the skeleton agent may initiate payments. Policy authorizes the capability; the
# ledger still enforces the cap, maker-checker, and payee allow-list (deterministic money path).
allow if {
	input.action == "payments.transfer"
	input.principal == "executive.cmo_agent"
}
