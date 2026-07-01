# Audit

The tamper-evident record of what happened: an append-only, hash-chained log of every governed action and decision.

## Language

**Audit Log**:
The append-only ledger of actions (principal, action, resource, outcome), each row chained by hash to the previous so tampering is detectable.
_Avoid_: log, history, trail (informally)

**Hash Chain**:
Each entry stores the prior entry's hash; a break in the chain proves an insertion or edit.
_Avoid_: signature, checksum
