# Slice 44 — Enforce per-business LLM budget at the gateway (before a model call)

**Why.** `ab_econ.within_llm_budget` (slice 42) is advisory. This wires it into the *live* model
path: a business-scoped model call is **denied before it happens** once the business's cumulative
LLM inference spend would breach its budget. Closes the ADR-0034 deferred "enforce at the Portkey
gateway" item.

**Decisions.**
1. **Budget lives on the `Blueprint`** (the per-business config, ab_growth): add
   `llm_budget_minor: int = Field(default=0, ge=0)`. **Secure default 0** — a business with no
   budget set cannot spend on inference (explicit opt-in), matching the skeleton's secure-by-default
   stance. Backward compatible (existing blueprints don't use the model path).
2. **Cumulative spend is metered in the ledger** as a per-business cost account
   `{business_id}:llm_spend`. A completed call books a balanced internal txn: debit
   `{business_id}:llm_spend (+cost)` / credit `{business_id}:cash (−cost)` (money conserved,
   `trial_balance()==0`; no `external:` payee, under the cap → maker-only, no checker needed).
3. **Pure enforcement gate** (`ab_gateway.llm_budget`): `gate_llm_spend(business_id, *, cost_minor,
   spent_minor, budget_minor)` raises `LLMBudgetExceeded` when `spent + cost > budget`, reusing
   `ab_econ.within_llm_budget` (projected spend). No I/O — the CI-tested core.
4. **Wiring** (`ab_gateway.tools.complete_for_business`): unknown business → `ToolDenied(400)`; read
   spent from the ledger cost account + budget from the blueprint; gate → over-budget raises
   `ToolDenied(402)` *before* calling the model; on pass call `model_gateway.complete`, then book
   the cost. Denial happens before any inference — no spend, no model call.

**Behaviors to test.**
- Pure gate (CI, infra-free): under budget → passes; exactly at budget → passes; projected over →
  raises `LLMBudgetExceeded` carrying business_id/spent/cost/budget.
- Wiring (integration, skips without infra): first call within budget completes and books cost to
  `{business_id}:llm_spend`; a later call that would breach is denied (402) and books nothing;
  unknown business → 400.

**Wiring.** `make llm-budget` — infra-free demo running the pure gate over a sequence of calls
(passes until the budget trips). ruff + mypy-strict clean; unique test basenames.
