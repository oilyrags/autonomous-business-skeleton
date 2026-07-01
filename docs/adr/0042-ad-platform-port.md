---
status: accepted
---

# Ad-platform port + stub + closed-loop attribution

Closes the P0 "ad platform integration / closed-loop attribution" gap. A business can run paid
acquisition: spend is booked to the ledger as a governed outbound payment, and attributed
conversions come back so CAC is real. PRD 0003; spec-driven.

## Decisions

- **New `ab_ads` context**, model-provider seam: `AdPlatform` **port** (`run(campaign) -> AdResult`)
  + `StubAdPlatform` (deterministic: `conversions = spend // cost_per_conversion`). A real
  Meta/Google Ads adapter implements the same `run`.
- **Ad spend is outbound money → governed**: `to_transaction` books debit `external:ad:<channel>`
  (+) / credit `{business_id}:cash` (−) with **maker-checker** (a distinct checker approves) —
  outbound to a new payee, so the ledger's own approval + allow-list rules apply (unlike inbound
  revenue). Idempotent on the campaign's external ref.
- **Closed-loop attribution**: `attributed_cac_minor(result) = spend // conversions`; the spend lands
  in `business_spend(bid).external_spend_minor`, which `ab_econ` already reads for CAC — so CAC is
  computed from real spend and real conversions end to end.
- **`AdSpendPlaced`** event (business-scoped, financial) — added to `ab_schemas` +
  `events.asyncapi.yaml`; the ADR-0037 contract test drove the spec addition.

## Verified

4 pure tests (stub conversion math; attributed CAC; spend books as business-scoped outflow feeding
`business_spend`; multi-campaign multi-business). AsyncAPI contract green (+3). `make ads` (in CI):
two businesses' campaigns spend ledger money and report conversions + CAC. Full suite 185 passed,
36 skipped; ruff + mypy strict clean (89 files).

## Deferred

Real ad-platform adapter (campaign API + conversion pixel); routing ad spend through the gateway's
governed business-spend path (`_gate_business_spend`) rather than a direct governed post; multi-touch
attribution.
