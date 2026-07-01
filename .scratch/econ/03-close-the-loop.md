# Slice 49 — Close the ledger → econ → portfolio loop

**Why.** Every piece now exists but nothing joins them: the ledger knows per-business spend
(slice 48), econ turns spend+revenue into a profitability verdict (slice 42), and `allocate` already
accepts an injected `unprofitable_business_ids` set (slice 43). This adds the one missing pure
connector + an end-to-end demonstration so capital allocation runs on **real ledger money**, not a
hand-picked set. Recommendations P1/P3 capstone.

**Decisions.**
1. **Pure connector in `ab_econ.core`:** `unprofitable_ids(economics: Iterable[UnitEconomics]) ->
   set[str]` — the businesses whose verdict is UNPROFITABLE. Trivial but named, tested, and the
   single definition of "who allocation must not fund". Keeps `ab_portfolio` decoupled (it still just
   receives a set).
2. **The loop is assembled by the caller**, staying dependency-directed: ledger `business_spend` →
   `UnitInputs` (+ injected revenue) → `economics` → `unprofitable_ids` → `allocate(..., that_set)`.
3. **Infra-free demo `make loop`** wiring the whole thing over an in-memory ledger: two businesses,
   one profitable and one bleeding on LLM+ad cost; both are experiment "winners" by score, but the
   bleeder is held because the *ledger* says it loses money. Shows the guardrail firing on real spend.

**Behaviors to test.**
- Pure: `unprofitable_ids` returns exactly the UNPROFITABLE business ids (empty when all healthy).
- End-to-end (pure, `InMemoryLedger`): seed two businesses' spend, derive economics with injected
  revenue, compute the unprofitable set, and `allocate` — the profitable winner gets INVEST_MORE, the
  money-losing winner is HELD ("fix economics before funding"). This is the capstone: allocation
  driven by real ledger spend.

ruff + mypy-strict clean; unique test basename `test_close_the_loop.py`.
