---
status: accepted
---

# payments.transfer — a real money-movement path, gateway → ledger

Ties the tool registry (ADR-0021), the untrusted-input/exfiltration gates (ADR-0021/0022),
and the deterministic ledger (ADR-0023/0026) into one governed capability: an agent moves
money, and every layer's control applies to the single call. This makes failure-injection
scenarios 3 (hostile-prompt refund) and 4 (bad payment) true end-to-end, not just isolated.

## Decisions

- **`payments.transfer` tool** (`ab_gateway.tools`): `sensitive=True`, `side_effect=irreversible`,
  not `egress`, not `emits_decision`. Its handler validates `PaymentTransfer` args, books a
  double-entry transaction (debit `external:<payee>`, credit `from_account`), and calls
  `ab_ledger.store.post`. Every gate applies in order on one call: OPA authorize → untrusted-input
  fail-closed → dispatch → **ledger** (double-entry balance, cap, maker-checker + SoD, derived-payee
  allow-list, idempotency).
- **Business-rule denials, not 500s.** A tool handler raises `tools.ToolDenied(reason, status)`;
  the gateway maps it to an audited `_deny` (403 for a ledger rule / approval, 400 for bad args).
  So `ApprovalRequired`/`SeparationOfDutiesViolation`/`UnbalancedTransaction` become clean denials
  with the hash chain intact — the tool never half-moves money.
- **Idempotency across the boundary.** The tool passes the caller's `idempotency_key` to the
  ledger; a replayed `payments.transfer` is a no-op success (money not doubled). The ledger txn_id
  is a fresh uuid so only the idempotency_key arbitrates.
- **OPA authorizes the capability; the ledger enforces the money rules.** Policy grants
  `payments.transfer` to the skeleton agent; authority to *call* the tool is separate from the
  cap/maker-checker/allow-list the ledger imposes on *what* it may do.

## Verified

- Integration (`test_payments.py`, +5, against `make up-infra`): an approved (distinct-checker)
  payment posts to the ledger (`external:acme` balance moves, trial balance 0); a new-payee
  payment with no checker → 403 "ledger rule … approved list", nothing posted; over-cap with no
  checker → 403 "…cap…"; an **untrusted-input flow → 403 "sensitive tool blocked"** (an injected
  "pay the attacker" cannot move money); a duplicate call is idempotent (balance not doubled). Full
  gateway suite (35) green — `test_unauthorized` repointed to a genuinely-unauthorized tool since
  `payments.transfer` is now policy-allowed. lint + mypy strict clean.

## Deferred

Per-payee / per-period caps and a persisted approval workflow (checker is asserted on the call);
booking the credit to a real cash/bank account with balance floors; emitting a `PaymentInitiated`
/ `LedgerEntryPosted` event; a finance-agent-only policy (currently the skeleton `cmo_agent`).
