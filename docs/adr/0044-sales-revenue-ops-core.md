---
status: accepted
---

# Sales & Revenue Operations core

Closes the P0 "Sales & Revenue Operations thin on autonomous pipeline management, quoting, closing,
renewals" gap. A deterministic pipeline moves an opportunity from lead to close and turns a won deal
into revenue. PRD 0003; spec-driven.

## Decisions

- **New `ab_sales` context, pure/deterministic** (no LLM — rule-based, evidence-carrying, in the
  `ab_growth`/`ab_econ` style). `run_pipeline(lead, *, min_fit_score, min_budget_minor) -> SaleResult`
  runs qualify → quote → close: a deal is **won** only when it fits the ICP, has budget, and the
  quote is within that budget; otherwise **lost** with the reason.
- **A won sale bridges to revenue**: `to_charge(result) -> Charge | None` produces an `ab_revenue`
  charge (None when lost), so the sales → revenue → ledger path is one composition — no new money
  code, reuses the revenue rail and its ledger booking.
- **Expansion/renewal**: `expansion_charge(result, *, uplift_minor)` produces an upsell charge on a
  won account (None otherwise) — the recommendation's renewal/expansion, minimally.
- **`SaleClosed`** event (business-scoped, financial, `stage ∈ {won, lost}`) — added to `ab_schemas`
  + `events.asyncapi.yaml`; the ADR-0037 contract test drove the spec addition.

## Verified

7 pure tests (won within budget; lost on fit; lost on over-budget quote; won→charge / lost→None; a
won sale booked through the revenue rail hits the ledger with `trial_balance()==0`; expansion only on
won; business-scoped event). AsyncAPI contract green (+3). `make sales` (in CI) runs four leads and
books the two won deals as ledger revenue. Full suite 201 passed, 36 skipped; ruff + mypy strict
clean (96 files).

## Deferred

Multi-stage pipeline persistence + stage-transition history; quoting logic beyond within-budget;
CRM/lead-source adapters behind a port; dunning/renewal scheduling.
