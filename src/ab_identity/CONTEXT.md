# Identity

Issues and verifies the identity every agent and service acts under — SPIFFE workload identity in the mesh, OIDC tokens for agent-to-gateway calls.

## Language

**SVID**:
A SPIFFE Verifiable Identity Document: the short-lived X.509 identity a workload presents for mTLS.
_Avoid_: cert, credential (too broad)

**Principal**:
The authenticated identity making a call (an agent id or workload), carried into every audit and policy decision.
_Avoid_: user, caller, subject (a subject_ref is the event's business subject)

**Trust Domain**:
The SPIFFE namespace (`spiffe://…`) that scopes which identities the mesh will issue and accept.
_Avoid_: realm, zone
