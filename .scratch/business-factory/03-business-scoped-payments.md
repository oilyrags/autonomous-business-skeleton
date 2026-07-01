# 03 — Business-scoped payments (Half 2)

Status: done (2026-07-01) — 5 integration tests, full gate + backward-compat
PRD: docs/prd/0002-business-factory.md (Half 2, was Out of Scope)  ·  Triage: ready-for-agent  ·  Blocked by: 01, 02

## What to build (one gateway change + integration tests)

Wire `ab_factory.can_spend`/`readiness` into `payments.transfer` so a business's payment is
blocked unless the business is launch-ready and within runway; the ledger's own controls still
apply on top.

- `PaymentTransfer.business_id: str | None = None` (optional; absent → current behavior).
- In `transfer_payment` when `business_id` set:
  - `business = ab_factory.store.get(business_id)`; None → `ToolDenied` ("unknown business", 400).
  - `cash = ledger.account_balance(f"{business_id}:cash")`.
  - live `readiness(business, cash_balance=cash, kill_switch_clear=not killswitch.is_killed(business_id),
    compliance_clear=not ropa.check())`; not ready → `ToolDenied` ("not launch-ready: reasons", 403).
  - `can_spend(business, amount_minor, cash_balance=cash)`; denied → `ToolDenied` (reason, 403).
  - `from_account = f"{business_id}:cash"` for the ledger txn (money leaves the business's cash).
- The ledger txn then applies cap / maker-checker / payee-allow-list / idempotency as today.

## Acceptance criteria

- [ ] A payment for an active, funded business → 200; `<business_id>:cash` decreases by the amount;
      `external:<payee>` increases; trial_balance 0.
- [ ] A payment for a kill-switched business → 403 "not launch-ready"; nothing posted.
- [ ] A payment exceeding remaining `<business_id>:cash` → 403 (can_spend runway denial); nothing posted.
- [ ] A payment for an unknown business_id → denied; nothing posted.
- [ ] A payment WITHOUT business_id still behaves as before (backward compatible).
- [ ] Integration tests vs `make up-infra`. ruff + mypy clean.

## Blocked by
01 (core), 02 (store).
