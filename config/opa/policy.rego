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
