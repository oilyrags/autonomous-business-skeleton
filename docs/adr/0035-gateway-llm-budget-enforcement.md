---
status: accepted
---

# Enforce per-business LLM budget at the gateway

Acting on the recommendations' **P3 cost control** and the ADR-0034 deferred item ("enforce
`within_llm_budget` at the Portkey gateway before a model call"). Turns the advisory econ guard into
a live control: a business-scoped model call is **refused before any inference** once the business's
cumulative LLM spend would breach its budget. Spec-driven (issue → tdd).

## Decisions

- **Budget on the `Blueprint`** (`ab_growth`, the per-business config): `llm_budget_minor: int =
  Field(default=0, ge=0)`. **Secure default 0** — a business cannot spend on inference until a
  budget is set (explicit opt-in, secure-by-default). Backward compatible.
- **Spend metered in the ledger** as a per-business cost account `{business_id}:llm_spend`. A
  completed call books a balanced internal txn: debit `{business_id}:llm_spend (+cost)` / credit
  `{business_id}:cash (−cost)`. Money is conserved; `trial_balance() == 0`; no `external:` payee and
  under the cap → maker-only (no checker). The budget therefore *tightens with use*.
- **Pure enforcement gate** `ab_gateway.llm_budget.gate_llm_spend(business_id, *, cost_minor,
  spent_minor, budget_minor)` — raises `LLMBudgetExceeded` (carrying the numbers) when
  `spent + cost > budget`, **reusing `ab_econ.within_llm_budget`** on the projected spend so the
  gateway and the economics context share one definition of "within budget". No I/O — the CI-tested
  core.
- **Wiring** `ab_gateway.tools.complete_for_business(principal, business_id, task_profile, prompt,
  *, cost_minor)`: unknown business → `ToolDenied(400)`; read spent from the ledger cost account +
  budget from the blueprint; gate → over-budget raises `ToolDenied(402)` **before** the model is
  invoked; on pass run `model_gateway.complete`, then meter the cost. Denial ⇒ no inference, no
  spend.

## Verified

- Pure gate (CI, infra-free): under / exactly-at budget pass; projected-over raises with context.
  3 tests.
- Wiring (integration, skips without infra): a within-budget call completes and meters spend to
  `{business_id}:llm_spend` (cash consumed, trial balance 0); a later call that would breach is
  denied (402) and books nothing; unknown business → 400. 3 tests.
- `make llm-budget` (in CI, infra-free) runs the gate over a sequence — 4 calls pass, the 5th is
  refused before inference. ruff + mypy strict clean (80 files); full suite 131 passed, 33 skipped.

## Deferred

Sourcing the *real* cost of a call (token accounting from the Portkey response) rather than an
injected `cost_minor`; publishing a Finance event for metered inference spend; gating on
launch-readiness as well as budget for model calls.
