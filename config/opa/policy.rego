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
# VULN-002: the input carries business_id so the policy can bind an agent to its tenants. The
# skeleton's executive operator acts portfolio-wide; `agent_businesses` scopes narrower principals.
allow if {
	input.action == "payments.transfer"
	input.principal == "executive.cmo_agent"
	principal_serves_business
}

# A principal may act when the call is not business-scoped (business_id null), for any business if
# portfolio-wide ("*"), or for a business explicitly granted to it.
principal_serves_business if input.business_id == null

principal_serves_business if {
	some b in agent_businesses[input.principal]
	b == "*"
}

principal_serves_business if {
	some b in agent_businesses[input.principal]
	b == input.business_id
}

# PRD 0007: the growth design agent may create governed experiment proposals, tenant-bound.
allow if {
	input.action == "growth.experiment.create"
	input.principal == "growth.experiment_design_agent"
	principal_serves_business
}

# PRD 0008: the product engineering agent may promote an initiative into a governed scaffold,
# tenant-bound (extend a business it serves, or mint a new one when business_id is null).
allow if {
	input.action == "product.initiative.promote"
	input.principal == "product.engineering_agent"
	principal_serves_business
}

# Per-principal tenant grants (mirror ab_gateway/authz.py; a real deployment loads this as OPA data).
agent_businesses := {
	"executive.cmo_agent": ["*"],
	"growth.experiment_design_agent": ["*"],
	"product.engineering_agent": ["*"],
}
