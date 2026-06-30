# Default-deny authorization for the walking skeleton.
# Slice 00: scaffold only — default deny, nothing allowed yet.
# Slice 01 adds the single allow rule (decision_registry.write for the skeleton
# agent principal); slice 02 exercises the deny path. The gateway calls
# POST /v1/data/ab/authz/allow with input {principal, action, resource, purpose}.
package ab.authz

import rego.v1

default allow := false
